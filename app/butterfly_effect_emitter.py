import json
import time
import os
from confluent_kafka import Producer

# --- CONFIGURACIÓN BASADA EN TU .ENV ---
# Usamos 'papilio_kafka:29092' y 'raw_events' como dice tu .env
conf = {'bootstrap.servers': "papilio_kafka:29092"} 
producer = Producer(conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"❌ Error: {err}")
    else:
        print(f"✅ Evento enviado al topic: {msg.topic()}")

def send_event(topic, data):
    producer.produce(topic, json.dumps(data).encode('utf-8'), callback=delivery_report)
    producer.flush()

# --- DATOS DE SIMULACIÓN (PapilioLogic Architecture) ---

# 1. El Buque (Atraca en Neo4j)
vessel_data = {
    "type": "buque",
    "mmsi": "235092348",
    "name": "Ocean-Star",
    "status": "en_ruta"
}

# 2. El Factor Externo (El "Aleteo" para DoWhy)
external_factor = {
    "type": "factor_externo",
    "factor_id": "STRIKE-SG-001",
    "name": "Huelga_Laboral",
    "subtype": "Huelga_Laboral",
    "severity": 0.9,
    "target_mmsi": "235092348"
}

# --- SIMULACIÓN DE EVOLUCIÓN ---
vessel_data = {
    "type": "buque",
    "mmsi": "235092348",
    "name": "Ocean-Star",
    "status": "RETRASADO" # <--- CAMBIAMOS EL ESTADO
}

external_factor = {
    "type": "factor_externo",
    "factor_id": "STRIKE-SG-002", # <--- NUEVO ID PARA OTRO EVENTO
    "subtype": "Cierre_Canal",
    "severity": 1.0,
    "target_mmsi": "235092348"
}

print("🚀 Disparando eventos hacia Papilio Logic AI...")

# Usamos 'raw_events' que es el que tienes en KAFKA_TOPIC_INPUT
send_event('raw_events', vessel_data)
time.sleep(1) 
send_event('raw_events', external_factor)

print("🏁 Hecho. Los datos ya deberían estar viajando hacia Neo4j.")