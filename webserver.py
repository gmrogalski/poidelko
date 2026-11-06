"""Lokalny panel HTTP: tylko odczyty, bez zewnetrznych bibliotek."""
import json
import socket


def open_server():
    server = socket.socket()
    try:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", 80))
        server.listen(2)
        server.settimeout(0.2)
        return server
    except Exception:
        server.close()
        raise


def response(client, status, content_type, body):
    if isinstance(body, str):
        body = body.encode("utf-8")
    header = ("HTTP/1.1 " + status + "\r\nContent-Type: " + content_type
              + "\r\nContent-Length: " + str(len(body))
              + "\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n")
    client.sendall(header.encode())
    client.sendall(body)


def handle(client, reading):
    client.settimeout(1)
    request = b""
    while b"\r\n\r\n" not in request and len(request) < 1024:
        chunk = client.recv(min(256, 1024 - len(request)))
        if not chunk:
            return
        request += chunk
    if b"\r\n\r\n" not in request:
        response(client, "431 Request Header Fields Too Large", "text/plain", "Zbyt dlugie naglowki")
        return
    parts = request.split(b"\r\n", 1)[0].split()
    if len(parts) != 3:
        response(client, "400 Bad Request", "text/plain", "Bledne zadanie")
        return
    if parts[0] != b"GET":
        response(client, "405 Method Not Allowed", "text/plain", "Tylko odczyt GET")
        return
    path = parts[1].split(b"?", 1)[0]
    if path in (b"/", b"/index.html"):
        with open("dashboard.html", "rb") as page:
            body = page.read()
        response(client, "200 OK", "text/html; charset=utf-8", body)
    elif path == b"/api/readings":
        response(client, "200 OK", "application/json; charset=utf-8", json.dumps(reading))
    elif path == b"/favicon.ico":
        response(client, "204 No Content", "image/x-icon", b"")
    else:
        response(client, "404 Not Found", "text/plain", "Nie znaleziono strony")
