import time

import sys

import os


def get_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return int(f.read()) / 1000.0
    except Exception as e:
        print("Erro ao ler temperatura:", e)
        return 0


def fan(state):
    gpio_path = "/sys/class/gpio/gpio18/value"

    try:
        # tenta garantir que GPIO existe
        if not os.path.exists("/sys/class/gpio/gpio18"):
            os.system("echo 18 > /sys/class/gpio/export")

        with open(gpio_path, "w") as f:
            f.write("1" if state else "0")

    except Exception as e:
        print("GPIO error:", e)


def main():
    # argumentos vindos do run.sh
    on_temp = float(sys.argv[1])
    off_temp = float(sys.argv[2])
    interval = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    fan_on = False

    print(f"FanShim iniciado | ON={on_temp} OFF={off_temp} interval={interval}s")

    while True:
        temp = get_temp()
        print(f"CPU Temp: {temp}°C")

        if temp >= on_temp and not fan_on:
            print("Fan ON")
            fan(True)
            fan_on = True

        elif temp <= off_temp and fan_on:
            print("Fan OFF")
            fan(False)
            fan_on = False

        time.sleep(interval)


if __name__ == "__main__":
    main()