#!/usr/bin/with-contenv bashio

ON_TEMP=$(bashio::config 'on_temperature')
OFF_TEMP=$(bashio::config 'off_temperature')

echo "Starting FanShim control"
echo "ON: $ON_TEMP °C | OFF: $OFF_TEMP °C"

python3 /fan_control.py "$ON_TEMP" "$OFF_TEMP"
