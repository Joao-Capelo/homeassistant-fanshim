FROM ghcr.io/hassio-addons/base-python:3.11.0

WORKDIR /app

COPY run.sh /run.sh
COPY fan_control.py /app/fan_control.py

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]