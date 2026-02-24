import json
import os
import time
from confluent_kafka import Consumer, KafkaException
from neo4j import GraphDatabase

# --- CONFIGURACIÓN ---
NEO4J_URI = os.getenv("PL_GRAPH_URI", "bolt://papilio_neo4j:7687")
NEO4J_USER = os.getenv("PL_GRAPH_USER", "neo4j")
NEO4J_PASS = os.getenv("PL_GRAPH_PASSWORD", "papilio_logic_2026")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "papilio_kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_INPUT", "papilio_logic_events")

class PapilioIngestor:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        self.conf = {
            'bootstrap.servers': KAFKA_BOOTSTRAP,
            'group.id': 'papiliologic_ingestor_v1',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True
        }
        self.consumer = Consumer(self.conf)
        self.consumer.subscribe([KAFKA_TOPIC, 'escalas'])

    def save_to_neo4j(self, data):
        with self.driver.session() as session:
            # 1. Lógica SIPLA / Escalas
            if data.get('source') in ['SIPLA_Simulador', 'escala'] or 'payload' in data:
                payload = data.get('payload', {})
                muelle_nombre = str(payload.get('muelle', 'Muelle_General')).strip()
                lloyd_id = payload.get('lloyd_id')
                
                query = """
                MERGE (b:Buque {lloyd_id: $lloyd_id})
                SET b.name = "Ship_" + $lloyd_id, b.muelle = $muelle
                MERGE (m:Muelle {nombre: $muelle})
                MERGE (b)-[r:SOLICITA_ATRAQUE]->(m)
                SET r.eta = $eta, r.etd = $etd, r.timestamp = $ts
                """
                session.run(query, 
                            lloyd_id=lloyd_id,
                            muelle=muelle_nombre,
                            eta=payload.get('eta'),
                            etd=payload.get('etd_estimada'),
                            ts=data.get('timestamp'))
                
                # LOG DE PROCESAMIENTO
                print(f"✅ [PROCESADO] Escala SIPLA: Buque {lloyd_id} asignado a {muelle_nombre}")

            # 2. Otros tipos (Buques AIS o Factores Externos)
            elif data.get('type') == 'factor_externo':
                subtype = data.get('subtype')
                print(f"✅ [PROCESADO] Factor Externo: {subtype} detectado (Gravedad: {data.get('severity')})")
            
            else:
                print(f"ℹ️ [INFO] Mensaje recibido de fuente: {data.get('source', 'Desconocida')}")

    def run(self):
        print(f"--- 📡 Ingestor Papilio Logic AI Activo ---")
        print(f"Conectado a Kafka: {KAFKA_BOOTSTRAP}")
        print(f"Escuchando topics: {KAFKA_TOPIC}, escalas")
        print(f"-------------------------------------------")
        
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None: continue
                if msg.error():
                    print(f"❌ [ERROR KAFKA] {msg.error()}")
                    continue

                try:
                    # Extraer información básica para el log de entrada
                    valor = json.loads(msg.value().decode('utf-8'))
                    timestamp = time.strftime('%H:%M:%S', time.localtime())
                    
                    print(f"📩 [{timestamp}] Mensaje recibido en topic '{msg.topic()}'")
                    self.save_to_neo4j(valor)
                    
                except json.JSONDecodeError:
                    print(f"⚠️ [WARNING] Mensaje omitido: No es un JSON válido")
                except Exception as e:
                    print(f"❌ [ERROR PROCESAMIENTO] {e}")

        except KeyboardInterrupt:
            print("\n🛑 Deteniendo Ingestor...")
        finally:
            self.consumer.close()
            self.driver.close()

if __name__ == "__main__":
    ingestor = PapilioIngestor()
    ingestor.run()