import json
import time
from confluent_kafka import Producer

# Configuración para conectar con el Kafka de Docker
conf = {'bootstrap.servers': "kafka:29092"}
producer = Producer(conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"Error al entregar mensaje: {err}")
    else:
        print(f"Evento enviado a {msg.topic()} [{msg.partition()}]")

def send_event(topic, data):
    producer.produce(topic, json.dumps(data).encode('utf-8'), callback=delivery_report)
    producer.flush()

# --- SIMULACIÓN DEL EFECTO MARIPOSA ---

# 1. El Buque (Situación Normal)
vessel_data = {
    "mmsi": "235092348",
    "name": "Ocean-Star",
    "status": "en_ruta",
    "eta": "2026-02-15T12:00:00Z",
    "last_port": "Singapur"
}

# 2. El Factor Externo (El "Aleteo" de la mariposa)
# Una huelga en el puerto de origen que causará un cuello de botella en el futuro
external_factor = {
    "factor_id": "STRIKE-SG-001",
    "type": "Huelga_Laboral",
    "location": "Canal de Suez",
    "severity": 0.9,
    "target_mmsi": "235092348", # Este factor afecta a nuestro buque
    "expected_delay_days": 10
}

print("Enviando eventos a PortNexus AI...")
send_event('portnexus.raw.vessels', vessel_data)
time.sleep(1) # Simular una pequeña pausa
send_event('portnexus.raw.external', external_factor)