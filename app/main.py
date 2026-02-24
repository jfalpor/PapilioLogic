import streamlit as st
import pandas as pd
import time

from engine import PapilioLogic_Engine

# --- CONFIGURACIÓN UI ---
st.set_page_config(page_title="Papilio Logic", layout="wide", page_icon="🚢")

if 'engine' not in st.session_state:
    st.session_state.engine = PapilioLogic_Engine()

st.title("🚢 Papilio Logic | Panel de Control")

lista_muelles = st.session_state.engine.obtener_muelles_reales()

# Barra lateral
with st.sidebar:
    st.header("🛠️ Configuración")
    if st.button("Resetear Interfaz"):
        st.session_state.engine.limpiar_base_de_datos()
        st.success("Grafo de Neo4j limpiado correctamente")
        time.sleep(3)
        st.rerun() # Recarga la app para limpiar las tablas visuales
    st.divider()
    st.caption("Entorno: Docker")

# Layout Principal
col_sim, col_view = st.columns([1, 2])

with col_sim:
    st.subheader("🕹️ Entrada de Datos")
    with st.form("main_form"):
        v_name = st.text_input("Buque", "")
        m_name = st.selectbox(
            "Muelle", 
            options=lista_muelles if lista_muelles else ["Sin muelles disponibles"]
        )
        f_type = st.selectbox("Factor de Riesgo", ["Ninguno", "Niebla", "Tormenta", "Huelga", "Avería"])
        g_level = st.slider("Gravedad", 0, 15, 0)
        
        submitted = st.form_submit_button("Ejecutar")

with col_view:
    st.subheader("🪞 Estado del Gemelo Digital")
    
    # Tabla vacía con la estructura de Papilio Logic
    columnas = ["Buque", "Muelle", "Factores", "Impacto"]
    df_vacio = pd.DataFrame(columns=columnas)
    
    st.dataframe(df_vacio, use_container_width=True, hide_index=True)
    
    if not submitted:
        st.info("Esperando entrada de datos...")

st.divider()
st.subheader("🦋 Análisis de Causalidad")
st.caption("Módulo de análisis local mediante Papilio Logic.")