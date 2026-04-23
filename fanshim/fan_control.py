#!/usr/bin/env python3
import argparse
import time
import os
import sys
import signal

TEMP_PATH = "/sys/class/thermal/thermal_zone0/temp"

# Try backends: libgpiod, periphery, RPi.GPIO, fallback to sysfs
try:
    import gpiod  # type: ignore
    HAS_LIBGPIOD = True
except Exception:
    HAS_LIBGPIOD = False

try:
    from periphery import GPIO as PeripheryGPIO  # type: ignore
    HAS_PERIPH = True
except Exception:
    HAS_PERIPH = False

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
    parser.add_argument("--gpio", type=int, default=18, help="GPIO pin number (BCM) or line offset")
    return parser.parse_args()


def get_temp():
    try:
        with open(TEMP_PATH) as f:
            return int(f.read().strip()) / 1000.0
    except Exception as e:
        print("Error reading temperature:", e, file=sys.stderr)
        return None


# periphery helpers
def setup_periphery(gpio):
    try:
        gpio = PeripheryGPIO(gpio, "out")
        gpio.set_value(0)
        return gpio
    except Exception as e:
        print("GPIO setup error (periphery):", e, file=sys.stderr)
        return None


def write_periphery(gpio, state):
    try:
        gpio.set_value(1 if state else 0)
        return True
    except Exception as e:
        print("GPIO write error (periphery):", e, file=sys.stderr)
        return False


def cleanup_periphery(gpio):
    try:
        gpio.pin.close()
    except Exception:
        pass


# libgpiod helpers
def setup_libgpiod(gpio):
    try:
        chip = gpiod.Chip("gpiochip0")
        line = chip.get_line(gpio)
        line.request(consumer="fanshim", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
        return chip, line
    except Exception as e:
        print("GPIO setup error (libgpiod):", e, file=sys.stderr)
        return None, None


def write_libgpiod(line, state):
    try:
        line.set_value(1 if state else 0)
        return True
    except Exception as e:
        print("GPIO write error (libgpiod):", e, file=sys.stderr)
        return False


def cleanup_libgpiod(line, chip):
    try:
        if line is not None:
            line.release()
        if chip is not None:
            chip.close()
    except Exception:
        pass


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


def cleanup_rpi_gpio():
    try:
        GPIO.cleanup()
    except Exception:
        pass


# Sysfs helpers (fallback)
def sysfs_available(gpio):
    base = f"/sys/class/gpio/gpio{gpio}"
    export = "/sys/class/gpio/export"
    value = os.path.join(base, "value")
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


def main():
    args = parse_args()

    if args.on_temp <= args.off_temp:
        print(
            f"Warning: on_temp ({args.on_temp}) <= off_temp ({args.off_temp}). Adjusting off_temp to {args.on_temp - 1}."
        )
        args.off_temp = args.on_temp - 1

    print(
        f"FanShim started | ON={args.on_temp} OFF={args.off_temp} INTERVAL={args.interval} GPIO={args.gpio}"
    )

    use_periph = False
    use_lib = False
    use_rpi = False
    use_sysfs = False
    lib_chip = None
    lib_line = None

    # Try libgpiod first (preferred on modern kernels)
    if HAS_LIBGPIOD:
        lib_chip, lib_line = setup_libgpiod(args.gpio)
        if lib_line is not None:
            use_lib = True
        else:
            print("libgpiod available but setup failed, will try other backends.", file=sys.stderr)

    # Try periphery next (useful on some Raspberry Pi OS installs)
    if not use_lib and HAS_PERIPH:
        periph_gpio = setup_periphery(args.gpio)
        if periph_gpio is not None:
            use_periph = True
        else:
            print("periphery available but setup failed, will try other backends.", file=sys.stderr)

    # Try RPi.GPIO next
    if not use_periph and not use_lib and HAS_RPI:
        use_rpi = setup_rpi_gpio(args.gpio)
        if not use_rpi:
            print("RPi.GPIO import succeeded but setup failed. Will try sysfs fallback.", file=sys.stderr)

    # Finally sysfs fallback
    if not use_periph and not use_lib and not use_rpi and sysfs_available(args.gpio):
        use_sysfs = ensure_sysfs(args.gpio)
        if not use_sysfs:
            print("Sysfs gpio setup failed.", file=sys.stderr)

    if not use_periph and not use_lib and not use_rpi and not use_sysfs:
        print(
            "No usable GPIO backend available. Ensure the add-on has access to /dev/gpiomem or /dev/gpiochip0, or sysfs GPIO writable.",
            file=sys.stderr,
        )

    fan_on = False

    def handle_sigterm(signum, frame):
        # Turn fan off on exit if possible
        try:
            if fan_on:
                if use_lib and lib_line is not None:
                    write_libgpiod(lib_line, False)
                elif use_rpi:
                    write_rpi_gpio(args.gpio, False)
                elif use_sysfs:
                    write_sysfs(args.gpio, False)
                elif use_periph:
                    write_periphery(periph_gpio, False)
        except Exception:
            pass
        # cleanup
        if use_lib:
            cleanup_libgpiod(lib_line, lib_chip)
        if HAS_RPI and use_rpi:
            cleanup_rpi_gpio()
        if use_periph:
            cleanup_periphery(periph_gpio)
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    # DEBUG: show available GPIO backends and device state
    print("Debug: HAS_PERIPH =", HAS_PERIPH)
    print("Debug: HAS_LIBGPIOD =", HAS_LIBGPIOD)
    print("Debug: HAS_RPI =", HAS_RPI)
    try:
        devs = [p for p in ["/dev/gpiomem", "/dev/gpiochip0"] if os.path.exists(p)]
        print("Debug: /dev files:", devs)
        for p in ["/dev/gpiomem", "/dev/gpiochip0"]:
            if os.path.exists(p):
                print(f"Debug: {p} perms:", oct(os.stat(p).st_mode & 0o777))
    except Exception as e:
        print("Debug: device check error:", e)
    try:
        export = "/sys/class/gpio/export"
        print("Debug: sysfs export exists:", os.path.exists(export), "writable:", os.access(export, os.W_OK))
    except Exception as e:
        print("Debug: sysfs check error:", e)

    while True:
        temp = get_temp()
        if temp is None:
            time.sleep(args.interval)
            continue

        print(f"CPU Temp: {temp:.1f}°C | Fan is {'ON' if fan_on else 'OFF'}")

        if temp >= args.on_temp and not fan_on:
            print("Turning fan ON")
            ok = False
            if use_lib and lib_line is not None:
                ok = write_libgpiod(lib_line, True)
            elif use_rpi:
                ok = write_rpi_gpio(args.gpio, True)
            elif use_sysfs:
                ok = write_sysfs(args.gpio, True)
            elif use_periph:
                ok = write_periphery(periph_gpio, True)
            if ok:
                fan_on = True
            else:
                print("Failed to turn fan ON", file=sys.stderr)

        elif temp <= args.off_temp and fan_on:
            print("Turning fan OFF")
            ok = False
            if use_lib and lib_line is not None:
                ok = write_libgpiod(lib_line, False)
            elif use_rpi:
                ok = write_rpi_gpio(args.gpio, False)
            elif use_sysfs:
                ok = write_sysfs(args.gpio, False)
            elif use_periph:
                ok = write_periphery(periph_gpio, False)
            if ok:
                fan_on = False
            else:
                print("Failed to turn fan OFF", file=sys.stderr)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()