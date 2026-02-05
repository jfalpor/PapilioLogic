import streamlit as st
import pandas as pd
from neo4j import GraphDatabase
import random
import os
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE CONEXIÓN ---
URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "papilio_logic_2026") 

class PapilioLogic_Engine:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    def close(self):
        self.driver.close()

    def limpiar_base_de_datos(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def simular_evento_manual(self, buque_nom, factor, muelle, delay):
        """Simulación manual compatible con PailioLogic"""
        with self.driver.session() as session:
            query = """
            MERGE (b:Buque {name: $b_nom})
            SET b.mmsi = $mmsi, b.status = 'Manual_Update'
            MERGE (f:FactorExterno {id: $f_id})
            SET f.tipo = $factor, 
                f.name = $factor, 
                f.location = 'Manual_Input', 
                f.gravedad = $gravedad
            MERGE (m:Muelle {id: $muelle})
            MERGE (f)-[:IMPACTA_EN]->(b)
            MERGE (b)-[:OCUPA]->(m)
            """
            session.run(query, 
                        b_nom=buque_nom, 
                        factor=factor, 
                        muelle=muelle,
                        gravedad=delay/15, 
                        mmsi=str(random.randint(1000,9999)),
                        f_id=f"{factor}_{buque_nom}_{random.randint(1,999)}")

    def consulta_libre_ln(self, pregunta):
        """Nueva Función: Consulta en Lenguaje Natural [cite: 2026-02-03]"""
        df_estado = self.obtener_analisis_causal()
        contexto_sistema = df_estado.to_string()
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434") + "/api/generate"
        prompt = f"""
        SISTEMA: PailioLogic
        FECHA: {fecha_actual}
        ESTADO DEL GRAFO: {contexto_sistema}
        PREGUNTA: {pregunta}
        
        Instrucción: Responde solo con los datos del sistema. Si no lo sabes, di que no hay datos.
        """
        
        try:
            # Implementación real de la petición que faltaba
            response = requests.post(url, json={
                "model": os.getenv("OLLAMA_MODEL", "llama3"),
                "prompt": prompt,
                "system": "Eres la interfaz de lenguaje natural de Papilio Logic. Solo hablas de los datos del sistema local. Responde de forma técnica, breve y directa al grano.",
                "stream": False,
                "keep_alive": -1
            }, timeout=240)
            
            if response.status_code == 200:
                return response.json().get('response', "Sin respuesta.")
            else:
                return f"Error del servidor Ollama: {response.status_code}"
                
        except Exception as e:
            return f"Error de conexión en LN: {str(e)}"

    def obtener_analisis_causal(self):
        """Consulta unificada para el Gemelo Digital"""
        with self.driver.session() as session:
            query = """
            MATCH (b:Buque)
            OPTIONAL MATCH (b)-[:SOLICITA_ATRAQUE|OCUPA]->(m:Muelle)
            OPTIONAL MATCH (f:FactorExterno)-[:IMPACTA_EN]->(b)
            RETURN 
                b.name AS buque, 
                collect(DISTINCT f.tipo) AS causas, 
                collect(DISTINCT f.gravedad) AS gravedades,
                COALESCE(b.muelle, m.name, m.id) AS muelle
            """
            result = session.run(query)
            return pd.DataFrame([dict(record) for record in result])

    def analizar_con_ollama(self, buque, causas, riesgo):
        """Componente H: Inferencia de Lenguaje Natural"""
        url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434") + "/api/generate"
        
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")

        prompt = f"""
DATOS DEL GEMELO DIGITAL (Sincronizados a: {fecha_actual}):
- SUJETO: Buque {buque} [cite: 2026-02-01]
- AMENAZA: {causas} [cite: 2026-02-01]
- INTENSIDAD: {riesgo}/1.0 (Escala de Causalidad) [cite: 2026-02-01]

TAREA DE ANÁLISIS EN TIEMPO REAL:
1. Identifica el 'Efecto Mariposa': ¿Cómo esta {causas} afectará a la logística antes de que ocurra el cuello de botella en la fecha {fecha_actual}? [cite: 2026-02-01]
2. Detecta Anomalías: Basado en la gravedad {riesgo}, ¿es un comportamiento esperado o crítico para este momento? [cite: 2026-02-01]
3. Recomendación Predictiva: Sugiere una acción preventiva inmediata para el atraque o la carga basada exclusivamente en lo que sabemos del sistema [cite: 2026-02-02].

REGLA DE ORO: Si no hay datos suficientes en el sistema para la fecha {fecha_actual}, responde que el sistema desconoce el impacto. No inventes información externa [cite: 2026-02-02].
"""
        
        try:
            response = requests.post(url, json={
                "model": os.getenv("OLLAMA_MODEL", "llama3"),
                "prompt": prompt,
                "system": ( "Eres el núcleo de inteligencia de PapilioLogic [cite: 2026-02-01]. "
                                      "Tu función es actuar como un Gemelo Digital Predictivo [cite: 2026-02-01]. "
                                      "Debes analizar cómo un factor externo (causa) genera un efecto mariposa en el flujo local del puerto [cite: 2026-02-01]. "
                                      "Usa terminología portuaria técnica (MMSI, ETA, estiba, calado, cuello de botella) y responde siempre en español."
                                      "Responde de forma técnica, breve y directa al grano."
                                    ),
                "stream": False,
                "keep_alive": -1
            }, timeout=240)
            return response.json().get('response', "Sin respuesta de la IA.")
        except Exception as e:
            return f"Error de conexión con Ollama: {str(e)}"

# --- INTERFAZ STREAMLIT (FUERA DE LA CLASE) ---
st.set_page_config(page_title="Papilio Logic AI", layout="wide")
engine = PapilioLogic_Engine()

with st.sidebar:
    st.header("🛠️ Mantenimiento")
    if st.button("🗑️ Reset Grafo"):
        engine.limpiar_base_de_datos()
        st.success("Grafo reseteado")
        st.rerun()

st.title("🚢 Papilio Logic AI: Control de Causalidad")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("🕹️ Simulador de Eventos")
    with st.form("sim_form"):
        buque = st.text_input("Nombre del Buque", f"Vessel_{random.randint(100,999)}")
        factor = st.selectbox("Factor de Riesgo", ["Niebla", "Tormenta", "Huelga", "Avería", "Cierre_Canal"])
        muelle = st.selectbox("Muelle Asignado", ["Muelle_Norte", "Muelle_Sur", "Terminal_Contenedores"])
        delay = st.slider("Gravedad del Suceso (1-15)", 1, 15, 3)
        if st.form_submit_button("Inyectar Suceso"):
            engine.simular_evento_manual(buque, factor, muelle, delay)
            st.rerun()

with col2:
    st.header("📊 Análisis de Riesgos en Tiempo Real")
    df = engine.obtener_analisis_causal()
    
    if not df.empty:
        # 1. Asegurar que las columnas existan antes de aplicar funciones
        if 'causas' in df.columns:
            df['causas_str'] = df['causas'].apply(lambda x: ", ".join(filter(None, x)) if x else "Ninguna")
        else:
            df['causas_str'] = "Ninguna"

        if 'gravedades' in df.columns:
            df['riesgo_max'] = df['gravedades'].apply(lambda x: max(x) if x and len(x)>0 else 0.0)
        else:
            df['riesgo_max'] = 0.0
        
        # ... resto del código (Alertas y Tabla)
        
        # Alertas de riesgo crítico
        for _, row in df.iterrows():
            if row['riesgo_max'] > 0.7:
                st.error(f"🚨 **RIESGO CRÍTICO**: {row['buque']} afectado por {row['causas_str']}")

        # Tabla principal
        st.table(df[['buque', 'causas_str', 'muelle']])
        
        # --- SECCIÓN DE OLLAMA ---
        st.divider()
        st.subheader("🧠 Consultar al Gemelo Digital (IA)")
        seleccion = st.selectbox("Selecciona un buque para análisis de impacto:", df['buque'].tolist())
        
        if st.button("🤖 Generar Informe de Causalidad"):
            datos_buque = df[df['buque'] == seleccion].iloc[0]
            with st.spinner('Ollama está analizando el efecto mariposa...'):
                informe = engine.analizar_con_ollama(
                    datos_buque['buque'], 
                    datos_buque['causas_str'], 
                    datos_buque['riesgo_max']
                )
                st.info(f"**Análisis de Papilio Logic:**\n\n{informe}")
    else:
        st.info("Sistema a la espera de datos (Kafka o Manual).")

# --- CONSOLA DE LENGUAJE NATURAL (MVP FINAL) ---
st.divider()
st.header("💬 Consola de Consulta LN (Papilio Logic)")
with st.container():
    pregunta_usuario = st.text_input("Haz una pregunta sobre el estado del puerto (ej: ¿Cuál es el buque con más riesgo ahora?)")
    
    if st.button("Consultar Sistema"):
        if pregunta_usuario:
            with st.spinner('Consultando al Gemelo Digital...'):
                respuesta = engine.consulta_libre_ln(pregunta_usuario)
                st.chat_message("assistant").write(respuesta)
        else:
            st.warning("Por favor, introduce una pregunta.")