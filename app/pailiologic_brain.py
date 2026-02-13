import os
from neo4j import GraphDatabase
import requests
import json

# --- CONFIGURACIÓN ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://papilio_neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "papilio_logic_2026")
OLLAMA_URL = "http://localhost:11434/api/generate" # O el nombre del contenedor

class PortNexusBrain:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

    def query_graph(self, cypher_query):
        with self.driver.session() as session:
            result = session.run(cypher_query)
            return [dict(record) for record in result]

    def ask_ollama(self, question):
        # 1. Obtenemos el contexto actual del puerto (Muelles y Calados)
        # Esto hace que Ollama siempre "sepa" lo último que hay en Neo4j
        context_data = self.query_graph("""
            MATCH (m:Muelle) 
            WHERE m.name IS NOT NULL
            RETURN m.name as muelle, m.calado_max as calado
        """)
        
        prompt = f"""
        Eres el motor predictivo de PortNexus AI. 
        Contexto actual del puerto (Datos de Neo4j):
        {json.dumps(context_data)}

        Pregunta del usuario: {question}
        Responde de forma concisa basada SOLO en los datos proporcionados.
        """

        response = requests.post(OLLAMA_URL, json={
            "model": "llama3", # o el modelo que uses
            "prompt": prompt,
            "stream": False
        })
        
        return response.json()['response']

if __name__ == "__main__":
    brain = PortNexusBrain()
    print("🤖 PortNexus Brain activo. Pregúntame sobre los muelles.")
    while True:
        user_input = input("❓: ")
        print(f"💡: {brain.ask_ollama(user_input)}")