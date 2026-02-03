#!/bin/bash

# Iniciar Ollama en segundo plano
ollama serve &

# Esperar a que el servicio esté disponible
echo "Esperando a que Ollama arranque..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
  sleep 2
done

# Descargar el modelo definido en el .env
echo "Descargando modelo: $OLLAMA_MODEL..."
ollama pull $OLLAMA_MODEL

# Mantener el proceso principal vivo
wait