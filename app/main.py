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

    def obtener_muelles_reales(self):
        """Obtiene nombres de muelles que no sean nulos para el simulador"""
        with self.driver.session() as session:
            query = "MATCH (m:Muelle) WHERE m.nombre IS NOT NULL RETURN m.nombre AS nombre ORDER BY m.nombre"
            result = session.run(query)
            return [record["nombre"] for record in result]

    def limpiar_base_de_datos(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def simular_evento_manual(self, buque_nom, factor, muelle, delay):
        with self.driver.session() as session:
            query = """
            MERGE (b:Buque {name: $b_nom})
            SET b.mmsi = $mmsi, b.status = 'Manual_Update'
            MERGE (f:FactorExterno {id: $f_id})
            SET f.tipo = $factor, 
                f.name = $factor, 
                f.location = 'Manual_Input', 
                f.gravedad = $gravedad
            MERGE (m:Muelle {nombre: $muelle})
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
        """Consulta Dinámica Optimizada: Filtra datos para evitar colapso de CPU"""
        with self.driver.session() as session:
            # 1. Traemos solo los datos clave, formateados como texto plano para ahorrar tokens
            query = """
            MATCH (n)
            WHERE n:Muelle OR n:Buque OR n:FactorExterno
            RETURN labels(n)[0] as tipo, properties(n) as p
            """
            result = session.run(query)
            
            # 2. Construimos un contexto humano, no un JSON pesado
            lineas_contexto = []
            for record in result:
                p = record['p']
                tipo = record['tipo']
                nombre = p.get('nombre') or p.get('lloyd_id') or "Desconocido"
                
                if tipo == 'Muelle':
                    lineas_contexto.append(f"- Muelle: {nombre}, Calado Máx: {p.get('calado_max')}m, Eslora Máx: {p.get('longitud_metros')}m")
                elif tipo == 'Buque':
                    lineas_contexto.append(f"- Buque: {nombre}, Eslora: {p.get('eslora')}m, Calado: {p.get('calado')}m")
                else:
                    lineas_contexto.append(f"- {tipo}: {nombre} ({p})")

            contexto_universal = "\n".join(lineas_contexto)
            
        url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434") + "/api/generate"
        
        # 3. Prompt ultra-enfocado
        prompt = f"""
        SISTEMA: Papilio Logic (Motor Predictivo)
        DATOS DEL PUERTO:
        {contexto_universal}

        PREGUNTA DEL USUARIO: {pregunta}

        INSTRUCCIÓN: Responde de forma técnica y muy breve (máximo 2 frases). 
        Si no encuentras el dato exacto, di simplemente que no consta en el grafo.
        """
        
        try:
            # 4. Petición con opciones de control de hardware
            response = requests.post(url, json={
                "model": "phi3",  # Forzamos el que ya tienes cargado en RAM
                "prompt": prompt,
                "system": "Eres el experto técnico de Papilio Logic. Tu prioridad es la precisión.",
                "stream": False,
                "options": {
                    "num_ctx": 4096,      # Límite de seguridad
                    "num_predict": 100,    # Respuesta corta = menos CPU
                    "temperature": 0,      # Sin alucinaciones
                    "num_thread": 4        # No satures todos los núcleos
                }
            }, timeout=60) # Bajamos el timeout porque ahora debe ser rápido
            
            if response.status_code == 200:
                return response.json().get('response', "IA sin respuesta.")
            return f"Error Ollama: {response.status_code}"
            
        except Exception as e:
            return f"Error de conexión: El motor está saturado. {str(e)}"

    def obtener_analisis_causal(self):
        with self.driver.session() as session:
            query = """
            MATCH (b:Buque)
            OPTIONAL MATCH (b)-[:SOLICITA_ATRAQUE|OCUPA]->(m:Muelle)
            OPTIONAL MATCH (f:FactorExterno)-[:IMPACTA_EN]->(b)
            RETURN 
                b.name AS buque, 
                collect(DISTINCT f.tipo) AS causas, 
                collect(DISTINCT f.gravedad) AS gravedades,
                COALESCE(b.muelle, m.name) AS muelle
            """
            result = session.run(query)
            return pd.DataFrame([dict(record) for record in result])

    def analizar_con_ollama(self, buque, causas, riesgo):
        # (Se mantiene igual que tu código original)
        url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434") + "/api/generate"
        prompt = f"Análisis de riesgo para {buque} con causa {causas} y nivel {riesgo}..."
        try:
            response = requests.post(url, json={
                "model": os.getenv("OLLAMA_MODEL", "llama3"),
                "prompt": prompt,
                "system": "Analista de riesgos portuarios.",
                "stream": False
            })
            return response.json().get('response', "Sin respuesta.")
        except: return "Error en análisis."

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Papilio Logic AI", layout="wide")
engine = PapilioLogic_Engine()

# Carga de muelles para el selector
lista_muelles_db = engine.obtener_muelles_reales()
if not lista_muelles_db:
    lista_muelles_db = ["Muelle_Norte", "Muelle_Sur"] # Fallback

with st.sidebar:
    st.header("🛠️ Mantenimiento")
    if st.button("🗑️ Reset Grafo"):
        engine.limpiar_base_de_datos()
        st.rerun()

st.title("🚢 Papilio Logic AI: Control de Causalidad")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("🕹️ Simulador de Eventos")
    with st.form("sim_form"):
        buque = st.text_input("Nombre del Buque", f"Vessel_{random.randint(100,999)}")
        factor = st.selectbox("Factor de Riesgo", ["Niebla", "Tormenta", "Huelga", "Avería", "Cierre_Canal"])
        # CORRECCIÓN: Ahora usa los muelles de la base de datos
        muelle = st.selectbox("Muelle Asignado", lista_muelles_db)
        delay = st.slider("Gravedad del Suceso (1-15)", 1, 15, 3)
        if st.form_submit_button("Inyectar Suceso"):
            engine.simular_evento_manual(buque, factor, muelle, delay)
            st.rerun()

with col2:
    st.header("📊 Análisis de Riesgos en Tiempo Real")
    df = engine.obtener_analisis_causal()
    
    if not df.empty:
        df['causas_str'] = df['causas'].apply(lambda x: ", ".join(filter(None, x)) if x else "Ninguna")
        df['riesgo_max'] = df['gravedades'].apply(lambda x: max(x) if x and len(x)>0 else 0.0)
        
        st.table(df[['buque', 'causas_str', 'muelle']])
        
        st.divider()
        st.subheader("🧠 Consultar al Gemelo Digital (IA)")
        seleccion = st.selectbox("Selecciona un buque:", df['buque'].tolist())
        
        if st.button("🤖 Generar Informe"):
            datos_buque = df[df['buque'] == seleccion].iloc[0]
            informe = engine.analizar_con_ollama(datos_buque['buque'], datos_buque['causas_str'], datos_buque['riesgo_max'])
            st.info(informe)
    else:
        st.info("Sistema a la espera de datos.")

st.divider()
st.header("💬 Consola de Consulta LN (Papilio Logic)")
pregunta_usuario = st.text_input("Pregunta (ej: ¿Cuál es el muelle con mayor calado?)")

if st.button("Consultar Sistema"):
    if pregunta_usuario:
        with st.spinner('Consultando al Gemelo Digital...'):
            respuesta = engine.consulta_libre_ln(pregunta_usuario)
            st.chat_message("assistant").write(respuesta)