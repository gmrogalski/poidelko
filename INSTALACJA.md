# Pierwsze uruchomienie poidełka — Pico 2 W / WH

Programy są przeznaczone dla MicroPythona uruchomionego na Pico, a nie dla zwykłego Pythona na komputerze. Czujniki i panel Wi-Fi sprawdzono na fizycznym zestawie 6 listopada 2026.

**Aktualnie na urządzeniu działa panel: http://ADRES_PICO/** (adres przydzielony przez domowy router może się zmienić).

Program startuje po włączeniu zasilania. Komputer lub telefon musi być w tej samej sieci domowej. Zasilanie USB wystarcza do pracy; komputer nie musi uruchamiać serwera.

Pliki bieżącego programu:

- `main.py` — automatyczny start;
- `app.py` — odczyty i obsługa sieci, ponawianie połączenia;
- `sensors.py` — czujnik poziomu I²C i analogowy TDS;
- `webserver.py` — lokalny serwer WWW;
- `dashboard.html` — panel odświeżający odczyty;
- `config.py` — lokalne ustawienia oraz hasła, pomijane przez Git;
- `config.example.py` — szablon bez danych domowej sieci.

Przygotowanie komputera oraz wcześniejsze proste programy diagnostyczne opisano poniżej.

## 1. MicroPython na Pico

1. Na razie pozostaw czujniki odłączone.
2. Pobierz stabilny plik UF2 z pierwszej sekcji Releases dla **Pico 2 W**, nie Pico W ani Pico 2: https://micropython.org/download/RPI_PICO2_W/
3. Przytrzymaj BOOTSEL na Pico, podłącz kabel USB do przesyłania danych, puść przycisk.
4. Na komputerze pojawi się dysk RP2350. Skopiuj na niego pobrany UF2. Pico zrestartuje się i dysk zniknie — to normalne.
5. Przy kolejnych podłączeniach USB nie trzymaj BOOTSEL.

## 2. VS Code na Macu

Otwórz folder `poidelko-pico` w VS Code. Otwórz Terminal → New Terminal i wykonaj po kolei:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install mpremote
mpremote connect list
mpremote run 01_dioda.py
```

Wymagany jest Python 3 na komputerze. Jeśli `python3` nie istnieje, zainstaluj Python 3 z https://www.python.org/downloads/ i otwórz terminal ponownie.

Pico powinno migać diodą co pół sekundy. Ctrl+C przerywa program. Pliki piszesz w VS Code, a `mpremote` uruchamia je na Pico przez USB. Przycisk „Run Python File” uruchamia zwykłego Pythona na komputerze i nie nadaje się do tych programów. Dodatkowa wtyczka do Pico nie jest potrzebna. Jeśli podłączono kilka urządzeń szeregowych, wybierz właściwy port z listy, np. `mpremote connect /dev/cu.usbmodem... run 01_dioda.py`.

## 3. Płytka stykowa i przewody

Odłącz USB przed zmianą połączeń. Włóż Pico nad środkową szczeliną płytki stykowej: dwa rzędy jego nóżek mają leżeć po przeciwnych stronach szczeliny. Otwory a–e w danym rzędzie są połączone, a f–j tworzą drugą grupę. Szyny boczne bywają przerwane w połowie.

Patrząc z góry na Pico, z gniazdem USB u góry: lewy rząd liczy się od 1 do 20 w dół, prawy od 21 do 40 w górę. **GP4 nie oznacza fizycznego pinu 4.**

| Czujnik | Sygnał | Typowy przewód Grove | Pico | Fizyczny pin |
| --- | --- | --- | --- | --- |
| Poziom | VCC | czerwony | 3V3(OUT) | 36 |
| Poziom | GND | czarny | wspólna szyna „−” → GND | 38 |
| Poziom | SDA | biały | GP4 | 6 |
| Poziom | SCL | żółty | GP5 | 7 |
| TDS | VCC | czerwony | 3V3(OUT) | 36 |
| TDS | GND | czarny | wspólna szyna „−” → GND | 38 |
| TDS | SIG / AOUT | żółty | GP26 / ADC0 | 31 |
| TDS | NC | biały | zostawić niepodłączony | — |

Oznaczenia na konkretnym module/adapterze mają pierwszeństwo przed kolorami. Oba czerwone przewody można połączyć przez jedną wspólną szynę, podłączoną do 3V3(OUT). Oba czarne przewody podłącz do wspólnej szyny „−”, a ją jednym przewodem do GND (pin 38). Korzystaj z jednego ciągłego odcinka szyny, bo niektóre płytki mają szyny rozdzielone w połowie. AGND i GND są wspólną masą Pico. Nie zasilaj czujnika I²C z 5 V: w tym układzie stosujemy 3,3 V.

Potrzebne są przewody Grove z rozdzielonymi końcówkami Dupont albo adapter. Sam przewód z dwiema białymi wtyczkami Grove nie pasuje do płytki stykowej. Nie wciskaj przewodów do złącza na siłę.

Do modułu TDS podłącz jego osobną sondę do dwupinowego gniazda. W wodzie umieszczaj sondę, a płytkę elektroniczną TDS i złącza trzymaj suche. Czujnik poziomu ustaw pionowo, częścią pomiarową w dół; podczas prób zachowaj złącze nad wodą. Pierwsze próby wykonuj w oddzielnym naczyniu bez ptaków.

## 4. Odczyty

Po podłączeniu czujników podłącz USB i wykonaj:

```sh
mpremote run 02_odczyty.py
```

Powinny pojawiać się wysokość wody w mm (krok 5 mm w zakresie 0–100 mm), napięcie czujnika TDS oraz szacowane ppm. Sprawdzaj zanurzenie czujnika poziomu przy dolaniu wody. Wskazanie 100 mm oznacza cały zakres czujnika, a nie automatycznie pełny zbiornik. W butelce o zmiennym przekroju wysokość nie jest proporcjonalna do liczby litrów.

Program odczytuje bezpośrednio adresy I²C 0x77 oraz 0x78. Standardowy skaner I²C MicroPythona może pominąć 0x78 — sama nieobecność w wyniku scan() nie dowodzi usterki.

TDS jest oszacowaniem na podstawie przewodności. Brak tu kalibracji i kompensacji temperatury wody; nie używamy temperatury procesora jako temperatury wody. Wynik nie wykrywa bakterii i nie orzeka o bezpieczeństwie wody. TDS mierz w spokojnej wodzie. Bez zanurzonej sondy nie interpretuj odczytu ppm. Przy komunikacie błędu I²C sprawdź przede wszystkim zasilanie, wspólną masę i SDA/SCL. W razie niestabilności sprawdzimy też podciąganie linii I²C; nie podciągaj ich do 5 V.

## 5. Wi-Fi — po udanej próbie czujników

**Bieżący panel:** ustawienia połączenia znajdują się w `config.py`. `WIFI_MODE = "STA"` oznacza domowy router. Aby docelowo uruchomić własną sieć Pico, ustaw `WIFI_MODE = "AP"`, wgraj zmieniony `config.py` i zrestartuj urządzenie:

```sh
mpremote fs cp config.py :config.py
mpremote reset
```

W trybie AP połącz komputer lub telefon z siecią wskazaną przez `AP_SSID`, używając hasła z `AP_PASSWORD`. Następnie otwórz http://192.168.4.1/. Brak dostępu do internetu w tej sieci jest normalny. Własną sieć Pico i zabezpieczenie WPA2 sprawdzono na urządzeniu; test z klientem Wi-Fi wykonano dotąd w trybie domowego routera.

Poniższy `03_wifi.py` jest wcześniejszą, osobną próbą samej łączności, bez panelu:

Wpisz nazwę sieci i hasło lokalnie w `03_wifi.py`, zapisz plik i uruchom:

```sh
mpremote run 03_wifi.py
```

Pico pokaże adres IP. To próba łączności, bez panelu WWW i wysyłania odczytów. Potrzebna jest sieć 2,4 GHz. Sieć szkolna z logowaniem przez stronę lub kontem ucznia może wymagać uzgodnienia z administratorem. Nie wysyłaj hasła do czatu ani do repozytorium.

## 6. Zapis na stałe

`mpremote run` uruchamia plik tymczasowo. Panel jest już zapisany na Pico. Aby wgrać bieżący projekt ponownie, z folderu `poidelko-pico` wykonaj:

```sh
mpremote fs cp sensors.py webserver.py dashboard.html cloud.py adafruit-ca.der config.py app.py main.py :
mpremote reset
```

Ten krok zastępuje istniejące pliki o tych nazwach na Pico. Do obserwowania komunikatów: `mpremote repl` (wyjście Ctrl+], przerwanie programu Ctrl+C). Nie otwieraj jednocześnie kilku terminali korzystających z tego samego portu. Polecenia `mpremote` mogą zatrzymać działający panel na czas programowania; po zakończeniu uruchom `mpremote reset`.

Na Pico pozostawiono też `main_serial_backup.py`: kopię pierwszego programu wypisującego pomiary wyłącznie po USB.

## Dokumentacja

- MicroPython dla Pico 2 W: https://micropython.org/download/RPI_PICO2_W/
- mpremote: https://docs.micropython.org/en/latest/reference/mpremote.html
- Poziom wody: https://wiki.seeedstudio.com/Grove-Water-Level-Sensor/
- TDS: https://wiki.seeedstudio.com/Grove-TDS-Sensor/
- Złącza Grove: https://wiki.seeedstudio.com/Grove_System/
