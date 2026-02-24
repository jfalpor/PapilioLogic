import json
import time
import random
import os
from datetime import datetime, timedelta
from kafka import KafkaProducer
from neo4j import GraphDatabase

# --- CONFIGURACIÓN DE ENTORNO ---
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "papilio_kafka:29092")
PL_GRAPH_URI = os.getenv("PL_GRAPH_URI", "bolt://neo4j:7687")
PL_GRAPH_USER = os.getenv("PL_GRAPH_USER", "neo4j")
PL_GRAPH_PASSWORD = os.getenv("PL_GRAPH_PASSWORD", "testpassword")
TOPIC_NAME = "papilio_logic_events"

# --- INICIALIZACIÓN DE CONEXIONES ---
print(f"⌛ Esperando infraestructura (Kafka & Neo4j)...")
time.sleep(15) 

try:
    # Conexión a Neo4j
    neo4j_driver = GraphDatabase.driver(PL_GRAPH_URI, auth=(PL_GRAPH_USER, PL_GRAPH_PASSWORD))
    
    # Conexión a Kafka
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        api_version=(2, 0, 2),
        acks=1,
        retries=5
    )
    print("✅ Conectado a Kafka y Neo4j.")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    exit(1)

# --- OBTENCIÓN DINÁMICA DE MUELLES ---
muelles = []
query = "MATCH (m:Muelle) WHERE m.nombre IS NOT NULL RETURN m.nombre AS nombre"

try:
    with neo4j_driver.session() as session:
        result = session.run(query)
        # Importante: strip() para asegurar que el string sea idéntico al del importador
        muelles = [record["nombre"].strip() for record in result]
        
    if not muelles:
        print("⚠️ No se encontraron muelles en Neo4j. Revisa la propiedad 'nombre'.")
        muelles = ["Muelle de Emergencia"]
    else:
        print(f"✅ Sincronizado. Muelles detectados: {muelles}")
except Exception as e:
    print(f"❌ Error al consultar muelles: {e}")
    muelles = ["Muelle de Emergencia"]

# --- BUCLE DE SIMULACIÓN ---
try:
    for i in range(5):
        ahora = datetime.now()
        eta = ahora + timedelta(hours=random.randint(1, 48))
        lloyd_id = str(random.randint(9000000, 9999999))
        
        muelle_elegido = random.choice(muelles)
        escala = {
            "source": "SIPLA_Simulador",
            "timestamp": ahora.isoformat(),
            "payload": {
                "lloyd_id": lloyd_id,            
                "eta": eta.isoformat(),
                "muelle": muelle_elegido, # Enviamos el nombre exacto
                "etd_estimada": (eta + timedelta(hours=random.randint(12, 48))).isoformat()
            }
        }
        
        # Envío al topic raw_events
        producer.send(TOPIC_NAME, key=lloyd_id.encode('utf-8'), value=escala)
        print(f"🚢 [Simulador] {i+1}/20 - Lloyd: {lloyd_id} -> {escala['payload']['muelle']}")
        
        time.sleep(2) # Reducido para pruebas más rápidas

finally:
    print("⏳ Cerrando conexiones...")
    producer.flush()
    neo4j_driver.close()
    print("🏁 Simulación finalizada.")