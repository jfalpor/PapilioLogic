from confluent_kafka import Consumer
from neo4j import GraphDatabase
import json

KAFKA_CONF = {
    'bootstrap.servers': "kafka:29092",
    'group.id': 'portnexus_logic_group',
    'auto.offset.reset': 'earliest'
}
NEO4J_URI = "bolt://neo4j:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password123"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def save_to_neo4j(topic, data):
    with driver.session() as session:
        if topic == 'portnexus.raw.vessels':
            query = """
            MERGE (b:Buque {mmsi: $mmsi})
            SET b.name = $name, b.eta = $eta, b.status = $status
            """
            session.run(query, mmsi=data.get('mmsi'), name=data.get('name'), 
                        eta=data.get('eta'), status=data.get('status'))
            print(f"⚓ Grafo: Buque {data.get('name')} sincronizado.")

        elif topic == 'portnexus.raw.external':
            # Mapeo de parámetros para evitar el error anterior
            delay = data.get('delay') or data.get('expected_delay_days') or 0
            
            query = """
            MATCH (b:Buque {mmsi: $target_mmsi})
            MERGE (f:FactorExterno {id: $type + "_" + $location})
            SET f.type = $type, f.location = $location, f.delay = $delay
            MERGE (f)-[r:AFECTA]->(b)
            SET r.timestamp = datetime()
            """
            session.run(query, 
                        target_mmsi=data.get('target_mmsi'),
                        type=data.get('type'),
                        location=data.get('location'),
                        delay=delay)
            print(f"🦋 Grafo: Causalidad detectada ({data.get('type')}) -> Barco {data.get('target_mmsi')}")

# Iniciar Consumidor
consumer = Consumer(KAFKA_CONF)
consumer.subscribe(['portnexus.raw.vessels', 'portnexus.raw.external'])

print("📡 PortNexus AI: Escuchando eventos... (Ctrl+C para parar)")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None: continue
        if msg.error(): continue
        
        save_to_neo4j(msg.topic(), json.loads(msg.value().decode('utf-8')))
finally:
    consumer.close()