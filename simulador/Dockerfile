FROM python:3.9-slim
WORKDIR /app
RUN pip install --no-cache-dir kafka-python
COPY simulador-sipla.py .
CMD ["python", "-u", "simulador-sipla.py"] 
# El -u es para ver los prints en tiempo real en los logs de Docker