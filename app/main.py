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
        
        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            submitted = st.form_submit_button("🚀 Ejecutar")
            if submitted:
                if v_name and m_name:
                    with st.spinner("Actualizando Gemelo Digital..."):
                        # Llamamos a la nueva función de guardado
                        st.session_state.engine.guardar_evento_buque(v_name, m_name, f_type, g_level)
                        st.success(f"Evento registrado: {v_name} en {m_name}")
                        time.sleep(1)
                        st.rerun() # Refrescamos para que aparezca en la tabla de la derecha
                else:
                    st.error("Por favor, introduce el nombre del Buque y selecciona un Muelle.")

        with col_btn2:
            submitted = st.form_submit_button("🔄 Refrescar")
            if submitted:
                st.rerun()

with col_view: 
    st.subheader("🪞 Estado del Gemelo Digital")
    
    # 1. Llamamos al método de la clase para obtener los datos frescos
    df_gemelo = st.session_state.engine.get_digital_twin_status()
    
    # 2. Mostramos el DataFrame (si está vacío, mostrará solo las cabeceras)
    st.dataframe(
        df_gemelo, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Impacto": st.column_config.TextColumn("⚠️ Impacto", help="Nivel de riesgo calculado por DoWhy")
        }
    )
    
    # 3. Lógica de estado
    if df_gemelo.empty:
        st.warning("El Gemelo Digital no tiene datos de muelles o buques registrados.")
    elif not submitted:
        st.info("Visualizando estado actual. Realiza una consulta para ver el efecto mariposa.")

st.divider()
st.subheader("🦋 Análisis de Causalidad")
st.caption("Módulo de análisis local mediante Papilio Logic.")

st.divider()
st.header("💬 Consola de Consulta LN (Papilio Logic)")
pregunta_usuario = st.text_input("Pregunta (ej: ¿Cuál es el muelle con mayor calado?)")

if st.button("Consultar Sistema"):
    if pregunta_usuario:
        with st.spinner('Consultando al Gemelo Digital...'):
            respuesta = engine.consulta_libre_ln(pregunta_usuario)
            st.chat_message("assistant").write(respuesta)