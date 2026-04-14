import time
import sys

on_temp = int(sys.argv[1])
off_temp = int(sys.argv[2])

fan_on = False


def get_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read()) / 1000.0
    except Exception as e:
        print("Erro ao ler temperatura:", e)
        return 0


def fan(state):
    gpio_path = "/sys/class/gpio/gpio18/value"

    try:
        with open(gpio_path, "w") as f:
            f.write("1" if state else "0")
    except Exception as e:
        print("GPIO error:", e)


print(f"FanShim iniciado | ON={on_temp} OFF={off_temp}")

while True:
    temp = get_temp()
    print(f"CPU Temp: {temp}")

    if temp >= on_temp and not fan_on:
        print("Fan ON")
        fan(True)
        fan_on = True

    elif temp <= off_temp and fan_on:
        print("Fan OFF")
        fan(False)
        fan_on = False

    time.sleep(5)