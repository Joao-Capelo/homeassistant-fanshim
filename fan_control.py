import time
import sys
import os

on_temp = int(sys.argv[1])
off_temp = int(sys.argv[2])

fan_on = False

def get_temp():
    with open("/sys/class/thermal/thermal_zone0/temp") as f:
        return int(f.read()) / 1000

def fan(state):
    # GPIO direto via sysfs (mais compatível que libs externas no HA OS)
    gpio = "/sys/class/gpio/gpio18/value"
    try:
        with open(gpio, "w") as f:
            f.write("1" if state else "0")
    except Exception as e:
        print("GPIO error:", e)

while True:
    temp = get_temp()
    print(f"Temp: {temp}")

    if temp >= on_temp and not fan_on:
        print("Fan ON")
        fan(True)
        fan_on = True

    elif temp <= off_temp and fan_on:
        print("Fan OFF")
        fan(False)
        fan_on = False

    time.sleep(5)
