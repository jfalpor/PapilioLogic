FROM python:3.9-slim
WORKDIR /app
RUN pip install --no-cache-dir kafka-python neo4j
COPY muelles.txt .
COPY muelles.py .
CMD ["python", "-u", "muelles.py"] 