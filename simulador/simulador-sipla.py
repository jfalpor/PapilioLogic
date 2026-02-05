import json
import time
import random
import os
from datetime import datetime, timedelta
from kafka import KafkaProducer

# CORRECCIÓN: Usamos el nombre del contenedor y el puerto interno 29092
# Por defecto ahora apunta a papilio_kafka:29092
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "papilio_kafka:29092")

# Espera de seguridad para asegurar que Kafka está listo
print(f"⌛ Esperando a Kafka en {KAFKA_BROKER}...")
time.sleep(10) 

try:
    producer = KafkaProducer(
        bootstrap_servers=['papilio_kafka:29092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        api_version=(2, 0, 2),
        acks=1, # Esperar al menos una confirmación del broker
        retries=5,
        request_timeout_ms=30000 # Darle tiempo para negociar metadata
    )
    print("✅ Conectado al bus de datos Papilio Logic.")
except Exception as e:
    print(f"❌ Error conectando a Kafka: {e}")
    exit(1)

muelles = ["Muelle_Sur_01", "Muelle_Sur_02", "Muelle_Norte_01", "Dique_Este", "Pantalan_A"]

# CORRECCIÓN: El topic debe ser 'escalas' según tu arquitectura Papilio Logic
TOPIC_NAME = "escalas"

for i in range(20):
    ahora = datetime.now()
    eta = ahora + timedelta(hours=random.randint(1, 48))
    # Generamos el ID del barco
    lloyd_id = str(random.randint(9000000, 9999999))
    escala = {
        "source": "SIPLA_Docker_App",
        "timestamp": ahora.isoformat(),
        "payload": {
            "lloyd_id": lloyd_id,            
            "eta": eta.isoformat(),
            "muelle": random.choice(muelles),
            "etd_estimada": (eta + timedelta(hours=random.randint(12, 48))).isoformat()
        }
    }
    
    # CORRECCIÓN: Usar la variable TOPIC_NAME
# Convertimos el lloyd_id a bytes manualmente en el send
    producer.send(TOPIC_NAME, key=str(lloyd_id).encode('utf-8'), value=escala)
    print(f"🚢 [Simulador] Enviada escala {i+1}/20 - Lloyd: {escala['payload']['lloyd_id']} al topic {TOPIC_NAME}")
    
    time.sleep(15)

# Al final de tu simulador-sipla.py
print("⏳ Vaciando buffer de mensajes...")
producer.flush()
time.sleep(2) # <--- Dale 2 segundos extra antes de que el contenedor muera
print("🏁 Simulación finalizada.")