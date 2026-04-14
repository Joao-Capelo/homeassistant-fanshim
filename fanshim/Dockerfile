ARG BUILD_FROM=python:3.11-slim
ARG BUILD_ARCH
FROM ${BUILD_FROM}

WORKDIR /app

# Install build deps and libgpiod dev (optional) so RPi.GPIO can be installed
RUN apt-get update && apt-get install -y \
    python3-dev \
    gcc \
    libgpiod-dev \
    && rm -rf /var/lib/apt/lists/*

# Install RPi.GPIO Python package (uses /dev/gpiomem)
RUN pip install RPi.GPIO

COPY run.sh /run.sh
COPY fan_control.py /app/fan_control.py

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]