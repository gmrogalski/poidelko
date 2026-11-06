"""MicroPython, Raspberry Pi Pico 2 W / WH. Bez podlaczonych czujnikow."""
from machine import Pin
from time import sleep

led = Pin("LED", Pin.OUT)
print("Pico dziala. Przerwij Ctrl+C.")
try:
    while True:
        led.toggle()
        sleep(0.5)
finally:
    led.off()
