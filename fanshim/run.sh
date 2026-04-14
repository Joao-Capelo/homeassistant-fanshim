#!/usr/bin/with-contenv bashio

ON_TEMP=$(bashio::config 'on_temperature')
OFF_TEMP=$(bashio::config 'off_temperature')

echo "FanShim Controller starting"
echo "ON: $ON_TEMP | OFF: $OFF_TEMP"

python3 /app/fan_control.py "$ON_TEMP" "$OFF_TEMP" "$CHECK_INTERVAL"