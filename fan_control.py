#! /usr/bin/env python3
import RPi.GPIO as GPIO
import time
import os
import signal
import sys
from configparser import ConfigParser


class config:
    FAN_PIN = 18        # BCM pin used to drive PWM fan
    WAIT_TIME = 1       # [s] Time to wait between each refresh
    PWM_FREQ = 25       # [Hz] 25Hz for Noctua PWM control

    OFF_TEMP = 40       # [°C] temperature below which to stop the fan
    MIN_TEMP = 45       # [°C] temperature above which to start the fan
    MAX_TEMP = 70       # [°C] temperature at which to operate at max fan speed
    FAN_LOW = 1
    FAN_HIGH = 100
    FAN_OFF = 0
    FAN_MAX = 100

    @classmethod
    def load(cls, filename="/etc/fan_control.cfg"):
        if not os.path.exists(filename):
            return
        parser = ConfigParser()
        parser.read(filename)
        try:
            section = parser['fan_control']
        except KeyError:
            print("Warning: No [fan_control] section found in config: {!r}"
                  .format(filename))
            return
        attrs = [attr for attr in dir(config) if attr[0].isupper()]
        for name, value in section.items():
            name = name.upper()
            if name not in attrs:
                print("Warning: Unknown config setting {!r}".format(name))
                continue
            try:
                value = int(value)
            except ValueError:
                print("Warning: Not an integer: {!r}={!r}"
                      .format(name, value))
                continue
            setattr(config, name, value)


C = config


def getCpuTemperature():
    with open('/sys/class/thermal/thermal_zone0/temp') as f:
        return float(f.read()) / 1000


def handleFanSpeed(fan, old_speed, temperature):
    if temperature > C.MIN_TEMP:
        gain = float(C.FAN_HIGH - C.FAN_LOW) / float(C.MAX_TEMP - C.MIN_TEMP)
        percent = min(100, round(temperature - C.MIN_TEMP))
        speed = round(C.FAN_LOW + percent * gain)

    elif temperature < C.OFF_TEMP:
        speed = C.FAN_OFF

    else:
        speed = old_speed

    if speed != old_speed:
        fan.start(speed)
        print("temp={:.1f}°C => fan-speed={}%".format(temperature, speed))

    return speed


def main():
    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
    signal.signal(signal.SIGUSR1, lambda *args: C.load())
    C.load()
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(C.FAN_PIN, GPIO.OUT, initial=GPIO.LOW)
        fan = GPIO.PWM(C.FAN_PIN, C.PWM_FREQ)
        speed = None
        while True:
            speed = handleFanSpeed(fan, speed, getCpuTemperature())
            time.sleep(C.WAIT_TIME)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()
