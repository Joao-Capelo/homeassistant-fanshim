#!/usr/bin/env python3
import argparse
import time
import os
import sys
import signal

TEMP_PATH = "/sys/class/thermal/thermal_zone0/temp"


# Try to use RPi.GPIO (works with /dev/gpiomem), fallback to sysfs
try:
    import RPi.GPIO as GPIO  # type: ignore
    HAS_RPI = True
except Exception:
    HAS_RPI = False


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


# Sysfs helpers (fallback)
def sysfs_available(gpio):
    base = f"/sys/class/gpio/gpio{gpio}"
    export = "/sys/class/gpio/export"
    direction = os.path.join(base, "direction")
    value = os.path.join(base, "value")
    # we can use sysfs only if export is writable or gpio already exported and value writable
    if os.path.exists(value) and os.access(value, os.W_OK):
        return True
    try:
        return os.access(export, os.W_OK)
    except Exception:
        return False


def ensure_sysfs(gpio):
    base = f"/sys/class/gpio/gpio{gpio}"
    export = "/sys/class/gpio/export"
    direction = os.path.join(base, "direction")
    try:
        if not os.path.exists(base):
            with open(export, "w") as f:
                f.write(str(gpio))
            time.sleep(0.1)
        if os.path.exists(direction):
            with open(direction, "w") as f:
                f.write("out")
        return True
    except Exception as e:
        print("GPIO setup error (sysfs):", e, file=sys.stderr)
        return False


def write_sysfs(gpio, state):
    value_path = f"/sys/class/gpio/gpio{gpio}/value"
    try:
        with open(value_path, "w") as f:
            f.write("1" if state else "0")
        return True
    except Exception as e:
        print("GPIO write error (sysfs):", e, file=sys.stderr)
        return False


# RPi.GPIO helpers
def setup_rpi_gpio(gpio):
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(gpio, GPIO.OUT)
        return True
    except Exception as e:
        print("GPIO setup error (RPi.GPIO):", e, file=sys.stderr)
        return False


def write_rpi_gpio(gpio, state):
    try:
        GPIO.output(gpio, GPIO.HIGH if state else GPIO.LOW)
        return True
    except Exception as e:
        print("GPIO write error (RPi.GPIO):", e, file=sys.stderr)
        return False


def main():
    args = parse_args()

    if args.on_temp <= args.off_temp:
        print(f"Warning: on_temp ({args.on_temp}) <= off_temp ({args.off_temp}). Adjusting off_temp to {args.on_temp - 1}.")
        args.off_temp = args.on_temp - 1

    print(f"FanShim started | ON={args.on_temp} OFF={args.off_temp} INTERVAL={args.interval} GPIO={args.gpio}")

    use_rpi = False
    use_sysfs = False

    if HAS_RPI:
        use_rpi = setup_rpi_gpio(args.gpio)
        if not use_rpi:
            print("RPi.GPIO import succeeded but setup failed. Will try sysfs fallback.", file=sys.stderr)

    if not use_rpi and sysfs_available(args.gpio):
        use_sysfs = ensure_sysfs(args.gpio)
        if not use_sysfs:
            print("Sysfs gpio setup failed.", file=sys.stderr)

    if not use_rpi and not use_sysfs:
        print("No usable GPIO backend available. Ensure the add-on has access to /dev/gpiomem or sysfs GPIO writable.", file=sys.stderr)

    fan_on = False

    def handle_sigterm(signum, frame):
        # Turn fan off on exit if possible
        try:
            if fan_on:
                if use_rpi:
                    write_rpi_gpio(args.gpio, False)
                elif use_sysfs:
                    write_sysfs(args.gpio, False)
        except Exception:
            pass
        # cleanup RPi.GPIO
        if HAS_RPI:
            try:
                GPIO.cleanup()
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    while True:
        temp = get_temp()
        if temp is None:
            time.sleep(args.interval)
            continue

        print(f"CPU Temp: {temp:.1f}°C | Fan is {'ON' if fan_on else 'OFF'}")

        if temp >= args.on_temp and not fan_on:
            print("Turning fan ON")
            ok = False
            if use_rpi:
                ok = write_rpi_gpio(args.gpio, True)
            elif use_sysfs:
                ok = write_sysfs(args.gpio, True)
            if ok:
                fan_on = True
            else:
                print("Failed to turn fan ON", file=sys.stderr)

        elif temp <= args.off_temp and fan_on:
            print("Turning fan OFF")
            ok = False
            if use_rpi:
                ok = write_rpi_gpio(args.gpio, False)
            elif use_sysfs:
                ok = write_sysfs(args.gpio, False)
            if ok:
                fan_on = False
            else:
                print("Failed to turn fan OFF", file=sys.stderr)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()