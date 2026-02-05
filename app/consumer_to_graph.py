import json
import os
from confluent_kafka import Consumer
from neo4j import GraphDatabase

# --- CONFIGURACIÓN (PapilioLogic Architecture) ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://papilio_neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "papilio_logic_2026")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "papilio_kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_INPUT", "raw_events")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def save_to_neo4j(data):
    with driver.session() as session:
        # 1. PROCESAMIENTO DE BUQUE (AIS/Estado)
        if data.get('type') == 'buque':
            query = """
            MERGE (b:Buque {mmsi: $mmsi})
            SET b.name = $name, b.status = $status
            """
            session.run(query, mmsi=data.get('mmsi'), name=data.get('name'), status=data.get('status'))
            print(f"⚓ Buque actualizado: {data.get('name')}")

        # 2. PROCESAMIENTO DE FACTOR EXTERNO (Efecto Mariposa)
        elif data.get('type') == 'factor_externo':
            query_factor = """
            MERGE (f:FactorExterno {id: $factor_id})
            SET f.tipo = $subtype, f.name = $subtype, f.gravedad = $severity, f.target_mmsi = $target_mmsi
            """
            session.run(query_factor, factor_id=data.get('factor_id'), subtype=data.get('subtype'), 
                        severity=data.get('severity'), target_mmsi=data.get('target_mmsi'))
            
            if data.get('target_mmsi'):
                query_rel = """
                MATCH (b:Buque {mmsi: $target_mmsi}), (f:FactorExterno {id: $factor_id})
                MERGE (f)-[:IMPACTA_EN]->(b)
                """
                session.run(query_rel, target_mmsi=data.get('target_mmsi'), factor_id=data.get('factor_id'))
                print(f"🦋 Factor {data.get('subtype')} vinculado a MMSI {data.get('target_mmsi')}")

        # 3. PROCESAMIENTO DE ESCALAS (SIPLA / Gemelo Digital)
        elif data.get('source') == 'SIPLA_Docker_App' or data.get('source') == 'escala':
            payload = data.get('payload', {})
            lloyd_id = payload.get('lloyd_id')
            muelle_nombre = str(payload.get('muelle')).strip()
            
            query_escala = """
            MERGE (b:Buque {lloyd_id: $lloyd_id})
            SET b.name = "Ship_" + $lloyd_id,
                b.muelle = $muelle  // Guardamos la propiedad en el buque para el DataFrame
            
            MERGE (m:Muelle {name: $muelle})
            
            // Relación unificada
            MERGE (b)-[r:SOLICITA_ATRAQUE]->(m)
            SET r.eta = $eta, 
                r.etd = $etd, 
                r.timestamp = $ts
            """
            session.run(query_escala, 
                        lloyd_id=lloyd_id, 
                        muelle=muelle_nombre, 
                        eta=payload.get('eta'), 
                        etd=payload.get('etd_estimada'),
                        ts=data.get('timestamp'))
            print(f"🚢 Gemelo Digital: Buque {lloyd_id} vinculado al Muelle {muelle_nombre}")

# --- LÓGICA DEL CONSUMER ---
conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP,
    'group.id': 'pailiologic_group_v4', # Cambiado para asegurar lectura limpia
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(conf)
consumer.subscribe([KAFKA_TOPIC, 'escalas'])

print(f"📡 Ingestor Papilio Logic AI activo en: {KAFKA_TOPIC} y escalas...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None: continue
        if msg.error():
            print(f"❌ Error: {msg.error()}")
            continue
            
        valor = json.loads(msg.value().decode('utf-8'))
        save_to_neo4j(valor)
except Exception as e:
    print(f"❌ Error crítico: {e}")
finally:
    consumer.close()
    driver.close()