FROM python:3.11-slim

WORKDIR /app

# Instalamos dependencias básicas
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el contenido de Proyecto_X a /app
COPY . .

# Comando corregido: ejecutamos Streamlit apuntando a la subcarpeta app/
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
