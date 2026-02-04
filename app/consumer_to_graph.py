import json
import os
from confluent_kafka import Consumer
from neo4j import GraphDatabase

# --- CONFIGURACIÓN (PailioLogic Architecture) ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "papilio_logic_2026")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "papilio_kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_INPUT", "raw_events")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def save_to_neo4j(data):
    with driver.session() as session:
        # 1. PROCESAMIENTO DE BUQUE
        if data.get('type') == 'buque':
            # Usamos 'name' para que Neo4j lo pinte en la bola morada
            query = """
            MERGE (b:Buque {mmsi: $mmsi})
            SET b.name = $name, b.status = $status
            """
            session.run(query, mmsi=data.get('mmsi'), name=data.get('name'), status=data.get('status'))
            print(f"⚓ Buque guardado: {data.get('name')}")

        # 2. PROCESAMIENTO DE FACTOR EXTERNO (LA BOLA NARANJA)
        elif data.get('type') == 'factor_externo':
            # IMPORTANTE: Seteamos 'name' con el valor de 'subtype' (ej: Huelga_Laboral)
            # Neo4j mostrará automáticamente este nombre dentro de la bola naranja.
            query_factor = """
            MERGE (f:FactorExterno {id: $factor_id})
            SET f.tipo = $subtype, 
                f.name = $subtype, 
                f.gravedad = $severity, 
                f.target_mmsi = $target_mmsi
            """
            session.run(query_factor, 
                        factor_id=data.get('factor_id'), 
                        subtype=data.get('subtype'), 
                        severity=data.get('severity'),
                        target_mmsi=data.get('target_mmsi'))
            
            print(f"🦋 Factor guardado: {data.get('subtype')}")

            # 3. CREAR LA UNIÓN AUTOMÁTICA
            if data.get('target_mmsi'):
                query_rel = """
                MATCH (b:Buque {mmsi: $target_mmsi}), (f:FactorExterno {id: $factor_id})
                MERGE (f)-[:IMPACTA_EN]->(b)
                """
                session.run(query_rel, target_mmsi=data.get('target_mmsi'), factor_id=data.get('factor_id'))
                print("🔗 Unión creada en el grafo.")

# --- LÓGICA DEL CONSUMER ---
conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP,
    'group.id': 'pailiologic_group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(conf)
consumer.subscribe([KAFKA_TOPIC])

print(f"📡 Ingestor activo en {KAFKA_TOPIC}...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None: continue
        valor = json.loads(msg.value().decode('utf-8'))
        save_to_neo4j(valor)
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    consumer.close()