# IoT
Project for FTN SIIT InternetOfThings 

## Opis projekta
Projektni zadatak ima za cilj implementaciju uređaja pametne kuće. Trenutno imlementirana kontrolna tačka 1. 
Senzori ispisuju stanje u konzoli, a aktuatori se kontrolišu putem komandne linije.
## Arhitektura
Aplikacija je podeljena na `core`, `devices` i `simulators`. 
Senzori i aktuatori se inicijalizuju kroz registry i rade u posebnim threadovima. 
GPIO pristup je izolovan kroz adapter radi podrške za realan i simuliran rad.
## Kako pokrenuti
Run main.py. Ispis senzora trenutno i komandama kotrola aktuatora.
## Config
Konfiguracija uređaja vrši se kroz fajl `settings.json`, gde se za svaki senzor i aktuator definišu pinovi i režim rada (simuliran ili realan). 
## Uređaji
### Senzori
- **DS1** - Door Sensor 
- **DPIR1** - Door Motion Sensor
- **DUS1** - Door Ultrasonic Sensor 
- **DMS** - Door Membrane Switch
### Aktuatori
- **DL** - Door Light 
- **DB** - Door Buzzer
