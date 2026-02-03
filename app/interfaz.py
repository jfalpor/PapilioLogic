# src/interfaz.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class PailioInterface:
    def __init__(self):
        self.url = os.getenv("OLLAMA_BASE_URL")
        self.model = os.getenv("OLLAMA_MODEL")
        self.system_prompt = (
            "Eres el motor PailioLogic. Solo hablas basándote en datos reales. "
            "Si no tienes datos en el contexto para responder una pregunta, "
            "di simplemente: 'No lo sé, no hay datos de causalidad registrados'."
        )

    def consultar(self, pregunta, contexto_del_grafo=""):
        # Unimos el prompt del sistema, el contexto de Neo4j y la pregunta
        prompt_completo = f"{self.system_prompt}\nContexto: {contexto_del_grafo}\nPregunta: {pregunta}"
        
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