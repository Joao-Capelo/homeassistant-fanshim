#!/usr/bin/env bash
set -e

# Use bashio when available (Home Assistant add-on runtime), otherwise fall back to environment variables.
if command -v bashio >/dev/null 2>&1; then
  ON_TEMP=$(bashio::config 'on_temperature')
  OFF_TEMP=$(bashio::config 'off_temperature')
  CHECK_INTERVAL=$(bashio::config 'check_interval')
else
  ON_TEMP=${ON_TEMPERATURE:-60}
  OFF_TEMP=${OFF_TEMPERATURE:-50}
  CHECK_INTERVAL=${CHECK_INTERVAL:-5}
fi

# Ensure defaults if variables are empty
ON_TEMP=${ON_TEMP:-60}
OFF_TEMP=${OFF_TEMP:-50}
CHECK_INTERVAL=${CHECK_INTERVAL:-5}

echo "FanShim Controller starting"
echo "ON: $ON_TEMP | OFF: $OFF_TEMP | INTERVAL: $CHECK_INTERVAL"

exec python3 /app/fan_control.py "$ON_TEMP" "$OFF_TEMP" --interval "$CHECK_INTERVAL"