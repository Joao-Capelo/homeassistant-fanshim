#!/usr/bin/env python3
import argparse
import time
import os
import sys

TEMP_PATH = "/sys/class/thermal/thermal_zone0/temp"


def parse_args():
    parser = argparse.ArgumentParser(description="FanShim controller")
    parser.add_argument("on_temp", type=int, help="Temperature (°C) to turn fan ON")
    parser.add_argument("off_temp", type=int, help="Temperature (°C) to turn fan OFF")
    parser.add_argument("--interval", type=float, default=5.0, help="Check interval in seconds")
    parser.add_argument("--gpio", type=int, default=18, help="GPIO pin number (BCM)")
    return parser.parse_args()


def get_temp():
    try:
        with open(TEMP_PATH) as f:
            return int(f.read().strip()) / 1000.0
    except Exception as e:
        print("Error reading temperature:", e, file=sys.stderr)
        return None


def ensure_gpio(gpio):
    base = f"/sys/class/gpio/gpio{gpio}"
    try:
        if not os.path.exists(base):
            with open("/sys/class/gpio/export", "w") as f:
                f.write(str(gpio))
            # small delay so sysfs appears
            time.sleep(0.1)
        direction_path = os.path.join(base, "direction")
        if os.path.exists(direction_path):
            with open(direction_path, "w") as f:
                f.write("out")
    except PermissionError:
        print("Permission error while configuring GPIO. Make sure the add-on has access to GPIO.", file=sys.stderr)
    except Exception as e:
        print("GPIO setup error:", e, file=sys.stderr)


def write_gpio_value(gpio, state):
    value_path = f"/sys/class/gpio/gpio{gpio}/value"
    try:
        with open(value_path, "w") as f:
            f.write("1" if state else "0")
    except Exception as e:
        print("GPIO write error:", e, file=sys.stderr)


def main():
    args = parse_args()

    if args.on_temp <= args.off_temp:
        print(f"Warning: on_temp ({args.on_temp}) <= off_temp ({args.off_temp}). Adjusting off_temp to {args.on_temp - 1}.")
        args.off_temp = args.on_temp - 1

    print(f"FanShim started | ON={args.on_temp} OFF={args.off_temp} INTERVAL={args.interval} GPIO={args.gpio}")

    ensure_gpio(args.gpio)

    fan_on = False
    while True:
        temp = get_temp()
        if temp is None:
            # if we cannot read temperature, wait and retry
            time.sleep(args.interval)
            continue

        print(f"CPU Temp: {temp:.1f}°C | Fan is {'ON' if fan_on else 'OFF'}")

        if temp >= args.on_temp and not fan_on:
            print("Turning fan ON")
            write_gpio_value(args.gpio, True)
            fan_on = True
        elif temp <= args.off_temp and fan_on:
            print("Turning fan OFF")
            write_gpio_value(args.gpio, False)
            fan_on = False

        time.sleep(args.interval)


if __name__ == "__main__":
    main()