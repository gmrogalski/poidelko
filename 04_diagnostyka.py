"""Krotka diagnostyka sprzetowa MicroPython; konczy sie samoczynnie."""
import sys
import network
from machine import Pin, ADC, I2C
from time import sleep_ms

print("MODEL:", sys.implementation._machine)
print("WERSJA:", sys.implementation.version)
print("OBSLUGA WIFI:", hasattr(network, "WLAN"))
led = Pin("LED", Pin.OUT)
for _ in range(4):
    led.on()
    sleep_ms(150)
    led.off()
    sleep_ms(150)
print("LED: zakonczono miganie")

bus = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
adc = ADC(Pin(26))
for attempt in range(3):
    print("PROBA:", attempt + 1)
    for address, count in ((0x77, 8), (0x78, 12)):
        try:
            print("I2C", hex(address), list(bus.readfrom(address, count)))
        except OSError as error:
            print("I2C", hex(address), "BLAD", error)
        sleep_ms(10)
    values = []
    for _ in range(31):
        values.append(adc.read_u16())
        sleep_ms(10)
    values.sort()
    median = values[15]
    print("ADC GP26: surowy=", median, "napiecie=", median * 3.3 / 65535)
    sleep_ms(500)
print("KONIEC DIAGNOSTYKI")
