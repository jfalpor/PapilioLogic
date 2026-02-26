import json
import time
from kafka import KafkaConsumer
from kafka import KafkaProducer
import requests
import sys

# --- CONFIGURACIÓN ---
KAFKA_BROKER = 'papilio_kafka:29092' 
OLLAMA_URL = "http://ollama:11434/api/generate"
TOPIC_IN = 'filtered_causality'

print("🦋 Papilio Logic: Iniciando conexión con el bus de datos...")

producer_final = KafkaProducer(
    bootstrap_servers=['papilio_kafka:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

try:
    consumer = KafkaConsumer(
        TOPIC_IN,
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='butterfly-reporter-v1', # Cambiar el ID de grupo fuerza a leer todo de nuevo
        # Añadimos estos para evitar que el script cierre la conexión prematuramente
        heartbeat_interval_ms=3000,
        session_timeout_ms=30000
    )
except Exception as e:
    print(f"❌ Error crítico de conexión: {e}")
    sys.exit(1)

def generate_butterfly_report(message_value):
    # 1. Intentamos obtener la lista de datos (soporta 'data' o el mensaje directo)
    eventos = message_value.get('data') if isinstance(message_value, dict) else None
    
    # Si no hay 'data', quizás el mensaje ES la lista
    if eventos is None and isinstance(message_value, list):
        eventos = message_value
        
    if not eventos or not isinstance(eventos, list):
        print(f"DEBUG: Contenido inesperado en el mensaje: {message_value}")
        return None

    # 2. Construimos el cuerpo del informe centrándonos en el "muelle"
    cuerpo_datos = ""
    for e in eventos:
        # Extraemos variables con valores por defecto para evitar errores
        buque = e.get('Buque', 'Desconocido')
        muelle = e.get('Muelle', 'No asignado')
        factor = e.get('Factores', 'Ninguno')
        impacto = e.get('Impacto', 'N/A')
        
        cuerpo_datos += f"- El buque {buque} en el {muelle} presenta factor {factor} con impacto {impacto}.\n"

    prompt = f"""
        Eres el analista jefe de Papilio Logic.
        Analiza la siguiente cadena de causalidad en el entorno marítimo:
        
        {cuerpo_datos}
        
        Redacta un informe ejecutivo breve (máximo 100 palabras) para el jefe de operaciones. 
        Explica cómo estos factores afectan la disponibilidad del muelle y la eficiencia del puerto.
    """
    
    try:
        print("🧠 Consultando a Ollama (llama3.2)...")
        response = requests.post(OLLAMA_URL, json={
            "model": "papilio-analyst",
            "prompt": prompt,
            "stream": False
        }, timeout=180)
        return response.json().get('response')
    except Exception as e:
        return f"❌ Error en Ollama: {e}"

print("🚀 Escuchando mensajes en 'filtered_causality'...")

# El bucle for sobre el consumer en kafka-python es bloqueante por naturaleza,
# si se sale es porque el consumer se cierra o pierde la conexión.
try:
    for message in consumer:
        print(f"📥 Evento detectado (Offset: {message.offset}).")
        val = message.value
        
        # DEBUG: Si falla, queremos ver las llaves del JSON
        if not isinstance(val, dict) or 'data' not in val:
            print(f"❌ Estructura inválida. Llaves encontradas: {list(val.keys()) if isinstance(val, dict) else 'No es un dict'}")
            print(f"📦 Contenido bruto: {val}")
            continue

        print("🧠 Consultando a Ollama (llama3.2)...")
        report = generate_butterfly_report(val)
        
        if report:
            print(f"\n--- INFORME PAPILIO LOGIC ---\n{report}\n")
            payload_informe = {
                "muelle": message.value.get('target', 'General'),
                "contenido": report,
                "timestamp": time.time()
            }
            producer_final.send('final_reports', payload_informe)
            print("📤 Informe enviado al topic 'final_reports'")
        else:
            # Si llega aquí, es que requests.post devolvió None o algo falló en la API
            print("⚠️ Ollama no devolvió texto. Revisa si el modelo 'llama3.2' está cargado.")
except KeyboardInterrupt:
    print("\n👋 Cerrando reportero de Papilio Logic...")
finally:
    consumer.close()