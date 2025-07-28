from machine import Pin
from utime import sleep

print("Hello, ESP32!")


trig = Pin(5, Pin.OUT)
echo = Pin(18, Pin.IN)
led_bomba = Pin(2, Pin.OUT)

