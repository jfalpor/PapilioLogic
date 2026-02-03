import streamlit as st
import pandas as pd
from neo4j import GraphDatabase
import random
import os
from datetime import datetime

# Configuración de conexión
URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
USER = "neo4j"
PASSWORD = "password123"

class PortNexus_Engine:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    def close(self):
        self.driver.close()

    def limpiar_base_de_datos(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def simular_evento_manual(self, buque_nom, factor, muelle, delay):
        """Simulación manual compatible con el esquema de Kafka"""
        with self.driver.session() as session:
            query = """
            MERGE (b:Buque {name: $b_nom})
            SET b.mmsi = $mmsi
            MERGE (f:FactorExterno {id: $f_id})
            SET f.type = $factor, f.location = 'Manual_Input', f.delay = $delay
            MERGE (m:Muelle {id: $muelle})
            MERGE (b)-[:AFECTADO_POR]->(f)
            MERGE (b)-[:OCUPA]->(m)
            """
            session.run(query, b_nom=buque_nom, factor=factor, muelle=muelle,
                        delay=delay, mmsi=str(random.randint(1000,9999)),
                        f_id=f"{factor}_{buque_nom}")

    def obtener_analisis_causal(self):
        """Une datos de Kafka y manuales"""
        with self.driver.session() as session:
            query = """
            MATCH (b:Buque)
            OPTIONAL MATCH (b)-[:AFECTADO_POR|AFECTA]-(f:FactorExterno)
            OPTIONAL MATCH (b)-[:OCUPA]->(m:Muelle)
            RETURN b.name as buque, 
                   collect(f.type) as causas, 
                   sum(f.delay) as retraso_total,
                   m.id as muelle
            """
            result = session.run(query)
            return pd.DataFrame([dict(record) for record in result])

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="PortNexus AI", layout="wide")
engine = PortNexus_Engine()

# Barra lateral
with st.sidebar:
    st.header("🛠️ Mantenimiento")
    if st.button("🗑️ Reset Grafo"):
        engine.limpiar_base_de_datos()
        st.rerun()

st.title("🚢 PortNexus AI: Control de Causalidad")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("🕹️ Simulador de Eventos")
    with st.form("sim_form"):
        buque = st.text_input("Nombre del Buque", f"Vessel_{random.randint(100,999)}")
        factor = st.selectbox("Factor de Riesgo", ["Niebla", "Tormenta", "Huelga", "Avería"])
        muelle = st.selectbox("Muelle Asignado", ["Muelle_Norte", "Muelle_Sur", "Terminal_Contenedores"])
        delay = st.slider("Días de retraso estimado", 1, 15, 3)
        if st.form_submit_button("Inyectar Suceso"):
            engine.simular_evento_manual(buque, factor, muelle, delay)
            st.rerun()

with col2:
    st.header("📊 Análisis de Riesgos en Tiempo Real")
    df = engine.obtener_analisis_causal()
    
    if not df.empty:
        # Formatear la columna causas para que se vea bien
        df['causas'] = df['causas'].apply(lambda x: ", ".join(x) if x else "Ninguna")
        
        # Mostrar alertas de anomalías (Retraso > 7 días)
        for _, row in df.iterrows():
            if row['retraso_total'] > 7:
                st.error(f"🚨 **ANOMALÍA**: El {row['buque']} acumula {row['retraso_total']} días de retraso por: {row['causas']}")

        st.table(df) # Usamos table para ver mejor las causas
    else:
        st.info("Sistema a la espera de datos (Kafka o Manual).")