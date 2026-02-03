import os
import json
from neo4j import GraphDatabase
from confluent_kafka import Consumer

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Usamos os.getenv para que use las llaves que Docker ya tiene
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://papilio_graph:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "papilio2026")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "papilio_kafka:29092")

# Inicializar Driver de Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def save_to_neo4j(topic, data):
    with driver.session() as session:
        if topic == "raw_events":
            query = """
            MERGE (b:Buque {mmsi: $mmsi})
            SET b.name = $name
            WITH b
            UNWIND $factors as f_data
            MERGE (f:FactorExterno {id: f_data.id})
            SET f.type = f_data.type, f.delay = f_data.delay
            MERGE (b)-[:AFECTADO_POR]->(f)
            """
            session.run(query, mmsi=data.get('mmsi'), name=data.get('name'), 
                        factors=data.get('factors', []))
            print(f"✅ Evento guardado en Grafo: {data.get('name')}")

# --- CONFIGURACIÓN CONSUMER ---
conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP,
    'group.id': 'portnexus_consumer_group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe(['raw_events'])

print("📡 PortNexus AI: Escuchando eventos... (Ctrl+C para parar)")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None: continue
        if msg.error():
            print(f"Error: {msg.error()}")
            continue

        # Procesar mensaje
        valor = json.loads(msg.value().decode('utf-8'))
        save_to_neo4j(msg.topic(), valor)

except KeyboardInterrupt:
    pass
finally:
    consumer.close()
    driver.close()