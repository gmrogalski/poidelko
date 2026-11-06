"""MicroPython. Grove 101020635 (I2C) i Grove 101020753 (analog).

Odczyt segmentow wedlug protokolu producenta:
https://wiki.seeedstudio.com/Grove-Water-Level-Sensor/
Przyblizenie TDS wedlug charakterystyki producenta:
https://wiki.seeedstudio.com/Grove-TDS-Sensor/

TDS nie jest ocena bezpieczenstwa wody. Brak kalibracji i pomiaru temperatury
wody: wynik ppm jest wstepnym oszacowaniem dla warunkow ok. 25 stopni C.
"""
from machine import ADC, I2C, Pin
from time import sleep, sleep_ms

adc = ADC(Pin(26))
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
THRESHOLD = 100
ADC_REFERENCE = 3.3  # nominalne napiecie odniesienia, do kalibracji


def water_level():
    # Czytamy oba adresy bezposrednio. scan() moze pominac adres 0x78,
    # poniewaz jest poza standardowym zakresem skanowania MicroPythona.
    low = i2c.readfrom(0x77, 8)
    sleep_ms(10)
    high = i2c.readfrom(0x78, 12)
    sleep_ms(10)
    values = list(low) + list(high)
    wet = [value > THRESHOLD for value in values]
    # Liczymy kolejne mokre segmenty od dolu, jak w przykladzie Seeed.
    count = 0
    for state in wet:
        if not state:
            break
        count += 1
    inconsistent = any(wet[count:])
    return count * 5, inconsistent, values


def tds():
    samples = []
    for _ in range(31):
        samples.append(adc.read_u16())
        sleep_ms(10)
    samples.sort()
    voltage = samples[len(samples) // 2] * ADC_REFERENCE / 65535
    ppm = (133.42 * voltage**3 - 255.86 * voltage**2 + 857.39 * voltage) * 0.5
    if voltage > 2.3 or ppm > 1000:
        return voltage, None
    return voltage, max(0, round(ppm))


print("Odczyty co ok. 2 s. Przerwij Ctrl+C.")
print("TDS: wynik orientacyjny, bez kalibracji i kompensacji temperatury.")
print("TDS: interpretuj odczyt tylko przy zanurzonej sondzie, w spokojnej wodzie.")
print("Poziom: mm zanurzenia aktywnego obszaru, NIE procent objetosci zbiornika.")
while True:
    try:
        mm, inconsistent, raw = water_level()
        if inconsistent:
            print("POZIOM: nierowne wskazania segmentow; sprawdz polozenie/osad.")
            print("Surowe odczyty:", raw)
        else:
            print("POZIOM: ok. {} mm / 100 mm".format(mm))
    except OSError as error:
        print("POZIOM: brak odpowiedzi I2C. Sprawdz 3V3/GND/SDA/SCL.", error)

    volts, ppm = tds()
    if ppm is None:
        print("TDS: poza zakresem; napiecie {:.3f} V".format(volts))
    else:
        print("TDS: ok. {} ppm; napiecie {:.3f} V".format(ppm, volts))
    print("---")
    sleep(2)
