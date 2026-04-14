#!/usr/bin/with-contenv bashio

ON_TEMP=$(bashio::config 'on_temperature')
OFF_TEMP=$(bashio::config 'off_temperature')
CHECK_INTERVAL=$(bashio::config 'check_interval')

if [ -z "$CHECK_INTERVAL" ]; then
  CHECK_INTERVAL=5
fi

echo "FanShim Controller starting"
echo "ON: $ON_TEMP | OFF: $OFF_TEMP | INTERVAL: $CHECK_INTERVAL"

python3 /app/fan_control.py "$ON_TEMP" "$OFF_TEMP" --interval "$CHECK_INTERVAL"