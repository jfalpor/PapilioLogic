import streamlit as st
import pandas as pd
from neo4j import GraphDatabase
import os
import random

# --- CONFIGURACIÓN DE CONEXIÓN ---
URI = os.getenv("PL_GRAPH_URI", "bolt://neo4j:7687")
USER = os.getenv("PL_GRAPH_USER", "neo4j")
PASSWORD = os.getenv("PL_GRAPH_PASSWORD", "testpassword")

# --- ENGINE ---
class PapilioLogic_Engine:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    def close(self):
        self.driver.close()

    def obtener_muelles_reales(self):
        with self.driver.session() as session:
            query = "MATCH (m:Muelle) WHERE m.nombre IS NOT NULL RETURN m.nombre AS nombre ORDER BY m.nombre"
            result = session.run(query)
            return [record["nombre"] for record in result]

    def limpiar_base_de_datos(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def get_digital_twin_status(self):
        query = """
            MATCH (b:Buque)
            // Buscamos la relación real que se ve en tu grafo
            OPTIONAL MATCH (b)-[:SOLICITA_ATRAQUE|ESTA_EN]->(m:Muelle)
            OPTIONAL MATCH (b)-[:AFECTADO_POR]->(f:FactorExterno)
            OPTIONAL MATCH (b)-[:SUFRE]->(r:Restriccion)
            RETURN 
                // Usamos id para asegurar que traiga Ship_95... si 'nombre' es nulo
                coalesce(b.name, b.id, "Buque desconocido") AS Buque, 
                coalesce(m.nombre, m.id, "En espera") AS Muelle, 
                collect(DISTINCT f.tipo) AS Factores,
                coalesce(r.nivel, "Estable") AS Impacto
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            # Convertimos el resultado de Neo4j directamente a un DataFrame de Pandas
            df = pd.DataFrame([dict(record) for record in result])
            
        # Post-procesamiento para que la tabla en Streamlit se vea limpia
        if not df.empty:
            # Convertimos la lista de factores en una cadena separada por comas
            df['Factores'] = df['Factores'].apply(lambda x: ", ".join(x) if x else "Ninguno")
        else:
            # Si no hay datos, devolvemos un DataFrame con las columnas correctas pero vacío
            df = pd.DataFrame(columns=["Buque", "Muelle", "Factores", "Impacto"])
            
        return df

    def guardar_evento_buque(self, buque_name, muelle_name, factor, gravedad):
        query = """
            // 1. Buscamos el buque por 'name' (según tu grafo)
            MERGE (b:Buque {name: $buque_name})
            
            // 2. BUSQUEDA FLEXIBLE DEL MUELLE:
            // Intentamos encontrar un muelle que ya exista con ese nombre
            WITH b
            MATCH (m:Muelle) 
            WHERE m.nombre = $muelle_name OR m.name = $muelle_name OR m.id = $muelle_name
            
            // 3. Creamos la relación SOLICITA_ATRAQUE con el muelle ENCONTRADO
            MERGE (b)-[:SOLICITA_ATRAQUE]->(m)
            SET b.muelle = m.nombre  // Guardamos el nombre real para el Gemelo Digital
            
            WITH b
            FOREACH (_ IN CASE WHEN $factor <> 'Ninguno' THEN [1] ELSE [] END |
                MERGE (f:FactorExterno {tipo: $factor})
                MERGE (b)-[:AFECTADO_POR]->(f)
                MERGE (r:Restriccion {nivel: $gravedad})
                MERGE (b)-[:SUFRE]->(r)
            )
        """
        with self.driver.session() as session:
            # Ejecutamos la consulta
            session.run(query, 
                        buque_name=buque_name, 
                        muelle_name=muelle_name, 
                        factor=factor, 
                        gravedad=gravedad)