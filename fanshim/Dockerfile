FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-dev \
    gcc \
    && apt-get clean

COPY run.sh /app/run.sh
COPY fan_control.py /app/fan_control.py

RUN chmod +x /app/run.sh

CMD [ "/app/run.sh" ]