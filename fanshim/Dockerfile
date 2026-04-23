ARG BUILD_FROM=python:3.11-slim-bullseye
ARG BUILD_ARCH
FROM ${BUILD_FROM}

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-dev \
    gcc \
    libgpiod2 \
    libgpiod-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python GPIO libraries (build wheels if needed)
RUN pip install --no-cache-dir RPi.GPIO python-periphery gpiod

COPY run.sh /run.sh
COPY fan_control.py /app/fan_control.py

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]