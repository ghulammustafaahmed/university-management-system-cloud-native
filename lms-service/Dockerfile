FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir flask pymysql flask-cors bcrypt requests
COPY app.py .
EXPOSE 5003 6003
CMD ["python", "app.py"]
