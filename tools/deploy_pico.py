"""Komputer, aktywne .venv: python tools/deploy_pico.py."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
from serial.tools import list_ports


def main():
    parser = argparse.ArgumentParser(description="Wgraj poidelko na Pico przez USB")
    parser.add_argument("--port", help="Port konkretnego Pico")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    tool = Path(sys.executable).parent / "mpremote"
    if not tool.exists():
        tool = shutil.which("mpremote")
    if not tool:
        parser.error("Zainstaluj requirements-dev.txt w aktywnym .venv.")
    port = args.port
    if not port:
        ports = [p.device for p in list_ports.comports() if p.vid == 0x2E8A]
        if len(ports) != 1:
            parser.error("Podlacz jedno Pico albo podaj --port.")
        port = ports[0]
    files = ["sensors.py", "webserver.py", "dashboard.html", "cloud.py",
             "adafruit-ca.der", "app.py", "config.py", "main.py"]
    if (root / "cloud_secrets.py").exists():
        files.append("cloud_secrets.py")
    for name in files:
        if not (root / name).exists():
            parser.error("Brak pliku: " + name)
    base = [str(tool), "connect", port]
    subprocess.run(base + ["fs", "cp"] + files + [":"], cwd=root, check=True)
    subprocess.run(base + ["reset"], cwd=root, check=True)
    print("Wgrano pliki i uruchomiono Pico. Podglad: mpremote repl")


if __name__ == "__main__":
    main()
