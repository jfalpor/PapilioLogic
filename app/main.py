import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN UI ---
st.set_page_config(page_title="Papilio Logic", layout="wide", page_icon="🚢")

st.title("🚢 Papilio Logic | Panel de Control")

# Barra lateral
with st.sidebar:
    st.header("🛠️ Configuración")
    st.button("Resetear Interfaz")
    st.divider()
    st.caption("Entorno: Docker")

# Layout Principal
col_sim, col_view = st.columns([1, 2])

with col_sim:
    st.subheader("🕹️ Entrada de Datos")
    with st.form("main_form"):
        v_name = st.text_input("Buque", "")
        m_name = st.text_input("Muelle", "")
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