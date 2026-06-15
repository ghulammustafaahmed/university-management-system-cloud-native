FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir flask flask-jwt-extended flask-sqlalchemy pymysql flask-cors bcrypt requests
COPY app.py .
EXPOSE 5001 6001
CMD ["python", "app.py"]
