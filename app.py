"""Poidełko Bioglow: czujniki, lokalny panel WWW, siec domowa lub wlasne Wi-Fi."""
import gc
import network
import rp2
import time
from machine import Pin
import config
from sensors import SensorReader
from webserver import open_server, handle
from cloud import CloudPublisher


def connect_wifi():
    rp2.country("PL")
    if config.WIFI_MODE == "AP":
        if len(config.AP_PASSWORD) < 8:
            raise ValueError("Haslo AP musi miec co najmniej 8 znakow.")
        wlan = network.WLAN(network.AP_IF)
        wlan.config(essid=config.AP_SSID, password=config.AP_PASSWORD, security=0x00400004)
        wlan.active(True)
        return wlan
    if config.WIFI_MODE != "STA":
        raise ValueError("WIFI_MODE: wybierz STA albo AP.")
    if not config.WIFI_SSID:
        raise ValueError("Uzupelnij WIFI_SSID w config.py.")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        start = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 20000 or wlan.status() < 0:
                wlan.disconnect()
                raise OSError("Nie udalo sie polaczyc z routerem.")
            time.sleep_ms(100)
    return wlan


def main():
    reader = SensorReader(config.ADC_REFERENCE, config.TDS_CALIBRATION_FACTOR,
                          config.LOW_LEVEL_MM)
    led = Pin("LED", Pin.OUT)
    cloud = CloudPublisher()
    server = None
    wlan = None
    seq = 0
    sample_time = time.ticks_ms()
    boot = sample_time
    retry = sample_time
    reading = reader.read()
    print("BIOGLOW: odczyty czujnikow i panel WWW")
    print("TDS: orientacyjnie, bez kalibracji i pomiaru temperatury wody.")
    try:
        while True:
            now = time.ticks_ms()
            if seq == 0 or time.ticks_diff(now, sample_time) >= config.SAMPLE_INTERVAL_MS:
                reading = reader.read()
                sample_time = time.ticks_ms()
                seq += 1
                print("POMIAR", seq, "poziom_mm=", reading["level_mm"],
                      "TDS_ppm=", reading["tds_ppm"], "V=", reading["tds_voltage"])

            connected = wlan is not None and (
                wlan.active() if config.WIFI_MODE == "AP" else wlan.isconnected())
            if not connected:
                led.off()
                if server:
                    server.close()
                    server = None
                if time.ticks_diff(time.ticks_ms(), retry) >= 0:
                    try:
                        print("WIFI: laczenie, tryb", config.WIFI_MODE)
                        wlan = connect_wifi()
                        print("WIFI: gotowe, PANEL http://" + wlan.ifconfig()[0] + "/")
                    except (OSError, ValueError) as error:
                        print("WIFI:", error, "Ponowna proba za 30 s.")
                    retry = time.ticks_add(time.ticks_ms(), 30000)
                time.sleep_ms(100)
                continue

            if server is None:
                try:
                    server = open_server()
                    led.on()
                except OSError as error:
                    print("HTTP:", error)
                    time.sleep_ms(500)
                    continue
            if config.WIFI_MODE == "STA":
                cloud.poll(reading, config.LOW_LEVEL_MM)
            try:
                client, _ = server.accept()
            except OSError as error:
                if error.args and error.args[0] not in (11, 110, 116):
                    print("HTTP accept:", error)
                continue

            try:
                payload = reading.copy()
                payload.update({"sequence": seq,
                    "sample_age_ms": time.ticks_diff(time.ticks_ms(), sample_time),
                    "uptime_s": time.ticks_diff(time.ticks_ms(), boot) // 1000,
                    "level_span_mm": 100, "low_level_mm": config.LOW_LEVEL_MM,
                    "mode": config.WIFI_MODE, "ip": wlan.ifconfig()[0]})
                handle(client, payload)
            except OSError as error:
                print("HTTP client:", error)
            finally:
                client.close()
                gc.collect()
    finally:
        if server:
            server.close()
        led.off()


if __name__ == "__main__":
    main()
