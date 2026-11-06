"""Wysylanie pojedynczego publicznego pomiaru do Adafruit IO przez HTTPS.
Nie publikuje hasel, kluczy, adresow IP ani nazwy sieci domowej.
"""
import gc
import json
import socket
import ssl
import time

HOST = "io.adafruit.com"
PUBLIC_FIELDS = ("level_mm", "level_status", "tds_ppm", "tds_voltage", "tds_status")


def send_all(stream, data):
    view = memoryview(data)
    while view:
        count = stream.write(view)
        if not count:
            raise OSError("Polaczenie HTTPS zamkniete")
        view = view[count:]


def open_tls():
    # Weryfikujemy lancuch CA oraz nazwe hosta; klucz API trafia wylacznie do TLS.
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.verify_mode = ssl.CERT_REQUIRED
    with open("adafruit-ca.der", "rb") as ca:
        ctx.load_verify_locations(cadata=ca.read())
    address = socket.getaddrinfo(HOST, 443, socket.AF_INET, socket.SOCK_STREAM)[0][-1]
    raw = socket.socket()
    raw.settimeout(4)
    try:
        raw.connect(address)
        return ctx.wrap_socket(raw, server_hostname=HOST)
    except Exception:
        raw.close()
        raise


class CloudPublisher:
    def __init__(self):
        try:
            import cloud_secrets as settings
            self.username = settings.AIO_USERNAME
            self.key = settings.AIO_KEY
            self.feed = settings.FEED_KEY
            self.interval = max(60, settings.PUBLISH_INTERVAL_S) * 1000
        except ImportError:
            self.username, self.key, self.feed = "", "", ""
            self.interval = 60000
        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
        if not all(c in allowed for c in self.username + self.feed):
            raise ValueError("Niepoprawna nazwa uzytkownika lub kanalu Adafruit")
        if "\n" in self.key or "\r" in self.key:
            raise ValueError("Klucz Adafruit nie moze zawierac nowej linii")
        self.enabled = bool(self.username and self.key and self.feed)
        self.next_due = time.ticks_ms()

    def publish(self, reading, low_level_mm=20):
        payload = {name: reading.get(name) for name in PUBLIC_FIELDS}
        payload.update({"schema": 1, "level_span_mm": 100, "low_level_mm": low_level_mm})
        body = json.dumps({"value": json.dumps(payload)}).encode()
        path = "/api/v2/" + self.username + "/feeds/" + self.feed + "/data"
        header = ("POST " + path + " HTTP/1.1\r\nHost: " + HOST
                  + "\r\nX-AIO-Key: " + self.key
                  + "\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body))
                  + "\r\nConnection: close\r\n\r\n").encode()
        stream = open_tls()
        try:
            send_all(stream, header)
            send_all(stream, body)
            line = stream.readline(256)
            parts = line.split()
            if len(parts) < 2 or parts[1] not in (b"200", b"201"):
                code = parts[1].decode() if len(parts) > 1 else "brak"
                raise OSError("Adafruit HTTP " + code)
        finally:
            stream.close()

    def poll(self, reading, low_level_mm=20):
        if not self.enabled or time.ticks_diff(time.ticks_ms(), self.next_due) < 0:
            return
        # Zarowno sukces, jak i blad ogranicza tempo kolejnych prob.
        self.next_due = time.ticks_add(time.ticks_ms(), self.interval)
        try:
            if time.gmtime()[0] < 2025:
                import ntptime
                ntptime.timeout = 2
                ntptime.settime()
            self.publish(reading, low_level_mm)
            print("CHMURA: wyslano pomiar do Adafruit IO")
        except (OSError, ValueError, ImportError) as error:
            print("CHMURA: nie wyslano pomiaru:", error)
        finally:
            gc.collect()
