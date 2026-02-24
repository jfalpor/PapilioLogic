import os
from neo4j import GraphDatabase

# Configuración de entorno Docker
URI = os.getenv("PL_GRAPH_URI", "bolt://neo4j:7687")
USER = os.getenv("PL_GRAPH_USER", "neo4j")
PASSWORD = os.getenv("PL_GRAPH_PASSWORD", "testpassword")

class PapilioLogicImporter: 
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def import_muelles(self, file_path):
        # USAMOS 'nombre' como propiedad clave
        query = """
        MERGE (m:Muelle {nombre: $nombre})
        SET m.longitud_metros = toFloat($metros),
            m.calado_min = toFloat($calado_min),
            m.calado_max = toFloat($calado_max),
            m.descripcion = $descripcion,
            m.ultima_actualizacion = datetime()
        RETURN m.nombre
        """
        
        if not os.path.exists(file_path):
            print(f"❌ Error: No se encuentra el archivo {file_path}")
            return

        with self.driver.session() as session:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line: continue
                    try:
                        parts = [p.strip() for p in line.split(',')]
                        descripcion = parts[-1]
                        calado_max = parts[-2]
                        calado_min = parts[-3]
                        metros = parts[-4].replace('.', '') 
                        nombre = ", ".join(parts[:-4]).strip() # .strip() clave aquí

                        session.run(query, 
                                    nombre=nombre, 
                                    metros=metros, 
                                    calado_min=calado_min, 
                                    calado_max=calado_max, 
                                    descripcion=descripcion)
                        print(f"✅ Muelle cargado: {nombre}")
                    except Exception as e:
                        print(f"❌ Error en línea: {line}. Detalle: {e}")

if __name__ == "__main__":
    importer = PapilioLogicImporter(URI, USER, PASSWORD)
    importer.import_muelles("muelles.txt")
    importer.close()