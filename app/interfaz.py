# src/interfaz.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class PapilioInterface:
    def __init__(self):
        self.url = os.getenv("OLLAMA_BASE_URL")
        self.model = os.getenv("OLLAMA_MODEL")
        self.system_prompt = (
            "Eres el motor PailioLogic. Solo hablas basándote en datos reales. "
            "Si no tienes datos en el contexto para responder una pregunta, "
            "di simplemente: 'No lo sé, no hay datos de causalidad registrados'."
        )

    def preguntar_al_gemelo(pregunta_usuario):
        # 1. Normalizamos la pregunta (para evitar el error de Pantanal vs Pantalan)
        pregunta_limpia = pregunta_usuario.replace("Pantanal", "Pantalan")
        
        # 2. Definimos la consulta al Grafo (Gemelo Digital)
        # Buscamos coincidencias aproximadas para que sea más flexible
        query = """
        MATCH (b:Buque)-[:SOLICITA_ATRAQUE]->(a:Muelle)
        WHERE a.name CONTAINS 'Pantalan'
        RETURN b.name as barco, b.lloyd_id as id
        """
        
        with driver.session() as session:
            result = session.run(query)
            datos = [f"Barco: {record['barco']} (ID: {record['id']})" for record in result]

        # 3. Construimos el contexto para Ollama
        if not datos:
            contexto = "No hay buques previstos en este momento."
        else:
            contexto = "Los buques previstos son: " + ", ".join(datos)

        # 4. Enviamos a OLLAMA con el rol de Gemelo Digital
        prompt_final = f"""
        Eres el Gemelo Digital de Papilio Logic AI. 
        Basándote en estos datos reales del puerto: {contexto}
        Responde a la siguiente pregunta del usuario: {pregunta_usuario}
        """
        
        # Aquí llamarías a tu instancia de Ollama
        # respuesta = ollama.generate(model='tu_modelo', prompt=prompt_final)
        return contexto # Por ahora retornamos los datos para confirmar
    
    def consultar(self, pregunta, contexto_del_grafo=""):
        # Unimos el prompt del sistema, el contexto de Neo4j y la pregunta
        prompt_completo = f"{self.system_prompt}\nContexto: {contexto_del_grafo}\nDime que quieres saber: {pregunta}"
        
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt_completo,
                    "stream": False
                }
            )
            return response.json().get('response', "Error al conectar con Ollama.")
        except Exception as e:
            return f"Error de conexión: {str(e)}"