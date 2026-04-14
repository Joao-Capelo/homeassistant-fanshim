import time
import os
import sys
import fanshim

on_temp = int(sys.argv[1])
off_temp = int(sys.argv[2])

fanshim.set_fan(False)

def get_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read()) / 1000
    except:
        return 0

fan_on = False

while True:
    temp = get_temp()
    print(f"Temp: {temp}°C")

    if temp >= on_temp and not fan_on:
        print("Fan ON")
        fanshim.set_fan(True)
        fan_on = True

    elif temp <= off_temp and fan_on:
        print("Fan OFF")
        fanshim.set_fan(False)
        fan_on = False

    time.sleep(5)
