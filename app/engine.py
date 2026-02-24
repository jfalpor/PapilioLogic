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