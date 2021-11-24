#! /usr/bin/env python3
import RPi.GPIO as GPIO
import time
import signal
import sys

WAIT_TIME = 1           # [s] Time to wait between each refresh
FAN_PINS = [18]         # BCM pins used to control fan
ON_TEMP = [43]          # Temperature above which a given pin is turned on
OFF_TEMP = [40]         # Temperature below which a given pin is turned off
# FAN_PINS = [0, 1, 2, 3]
# ON_TEMP = [3, 13, 23, 33]
# OFF_TEMP = [0, 10, 20, 30]


def getCpuTemperature():
    with open('/sys/class/thermal/thermal_zone0/temp') as f:
        return float(f.read()) / 1000


def handleFanSpeed(cur_level, temp):
    on = next((i for i, t in enumerate(ON_TEMP) if t > temp), len(FAN_PINS))
    off = next((i for i, t in enumerate(OFF_TEMP) if t > temp), len(FAN_PINS))
    if on > cur_level:
        new_level = on
    else:
        new_level = min(off, cur_level)

    if cur_level != new_level:
        if cur_level != 0:
            GPIO.output(FAN_PINS[cur_level - 1], GPIO.LOW)
        if new_level != 0:
            GPIO.output(FAN_PINS[new_level - 1], GPIO.HIGH)
        print("temp={:.1f}°C => fan-level={}".format(temp, new_level))

    return new_level


def main():
    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for pin in FAN_PINS:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

        level = 0
        while True:
            temp = getCpuTemperature()
            level = handleFanSpeed(level, temp)
            time.sleep(WAIT_TIME)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()
