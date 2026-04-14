FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY fan_control.py /app/fan_control.py

CMD ["python3", "/app/fan_control.py", "60", "50"]