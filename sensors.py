"""Grove 101020635 + 101020753; interfejsy wedlug dokumentacji Seeed.
Wynik TDS jest orientacyjny, bez kompensacji temperatury wody.
"""
from machine import ADC, I2C, Pin
from time import sleep_ms


class SensorReader:
    def __init__(self, reference=3.3, calibration=1.0, low_level_mm=20):
        self.bus = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
        self.adc = ADC(Pin(26))
        self.reference = reference
        self.calibration = calibration
        self.low_level_mm = low_level_mm

    def read(self):
        result = {"level_mm": None, "level_status": "error",
                  "tds_ppm": None, "tds_voltage": None, "tds_status": "error"}
        try:
            low = self.bus.readfrom(0x77, 8)
            sleep_ms(10)
            high = self.bus.readfrom(0x78, 12)
            wet = [v > 100 for v in list(low) + list(high)]
            count = 0
            for state in wet:
                if not state:
                    break
                count += 1
            if any(wet[count:]):
                result["level_status"] = "inconsistent"
            else:
                result["level_mm"] = count * 5
                result["level_status"] = "low" if count * 5 < self.low_level_mm else "ok"
        except OSError:
            pass

        try:
            samples = []
            for _ in range(31):
                samples.append(self.adc.read_u16())
                sleep_ms(10)
            samples.sort()
            voltage = samples[15] * self.reference / 65535
            result["tds_voltage"] = round(voltage, 3)
            ppm = (133.42 * voltage**3 - 255.86 * voltage**2 + 857.39 * voltage) * 0.5 * self.calibration
            if voltage > 2.3 or ppm > 1000:
                result["tds_status"] = "out_of_range"
            else:
                result["tds_ppm"] = max(0, round(ppm))
                result["tds_status"] = "approximate"
        except OSError:
            pass
        return result
