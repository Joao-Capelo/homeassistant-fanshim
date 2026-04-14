FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    python3-dev \
    gcc \
    && pip install --no-cache-dir rpi-gpio fanshim || true \
    && apt-get clean

COPY run.sh /
COPY fan_control.py /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
