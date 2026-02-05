# 📑 Catálogo de Topics - PapilioLogic

Este documento detalla los canales de datos (topics) que fluyen a través de **Apache Kafka** dentro de la arquitectura **Papilio Logic**.

---

## 🚢 1. Topic: `escalas`

### **Descripción**
Este es el canal principal de planificación logística. Contiene las declaraciones de llegada, estancia y salida de los buques en el puerto. Es la fuente de verdad para la agenda del puerto.

### **Metadatos Técnicos**
* **Productor (Bloque A):** Sistema SIPLA (Gestión Portuaria).
* **Consumidor Principal:** Módulo Ingestor / Parser (C).
* **Destino Final:** Grafo de relaciones Neo4j.
* **Particiones:** 1 (Entorno de desarrollo local).
* **Factor de Replicación:** 1.
* **Política de Retención:** 7 días (`604800000 ms`).

### **Esquema de Datos (JSON)**
Cada mensaje enviado por SIPLA debe seguir esta estructura para ser procesado por el motor de inferencia:

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `lloyd_id` | String | Identificador único internacional del buque. |
| `eta` | String | *Estimated Time of Arrival*. Formato ISO8601. |
| `muelle` | String | Identificador del muelle en el que se desea operar. |
| `etd_estimada` | String | *Estimated Time of Departure*. Salida prevista. |

**Ejemplo de mensaje:**
```json
{
  "source": "SIPLA",
  "timestamp": "2026-02-04T17:20:00Z",
  "payload": {
    "lloyd_id": "9234567",
    "eta": "2026-02-05T08:00:00Z",
    "muelle_solicitado": "Muelle_Sur_02",
    "etd_estimada": "2026-02-06T12:00:00Z"
  }
}