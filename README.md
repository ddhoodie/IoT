# IoT
Projekat za FTN SIIT InternetOfThings.

## Opis projekta
Projektni zadatak ima za cilj implementaciju uređaja pametne kuće. Trenutno implementirana kontrolna tačka 1.
Senzori ispisuju stanje u konzoli i šalju podatke na MQTT broker, a aktuatori se kontrolišu putem komandne linije.

## Arhitektura
Aplikacija je podeljena na `core`, `devices`, `simulators` i `backend`.
Senzori i aktuatori se inicijalizuju kroz registry i rade u posebnim threadovima.
GPIO pristup je izolovan kroz adapter radi podrške za realan i simuliran rad.
`backend/server.py` prikuplja podatke sa MQTT brokera i čuva ih u InfluxDB bazi.

## Kako pokrenuti

### 1. Pokretanje infrastrukture (Docker Compose)
Potrebno je imati instaliran Docker. Pokrenite RabbitMQ i InfluxDB komandom:
```bash
docker-compose up -d
```
Ovo će pokrenuti:
- **RabbitMQ** (MQTT broker) na portu `1883`.
- **InfluxDB** na portu `8086`.
- **Grafana** na portu `3000`.

### 2. Instalacija zavisnosti
Preporučuje se korišćenje virtuelnog okruženja:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```
Instalirajte potrebne biblioteke:
```bash
pip install flask paho-mqtt influxdb-client
```

### 3. Pokretanje Backend servera
U novom terminalu (uz aktiviran venv) pokrenite:
```bash
python backend/server.py
```
Server će slušati MQTT poruke i automatski kreirati buckete u InfluxDB bazi za svaki tip senzora.

### 4. Pokretanje simulatora uređaja
U novom terminalu (uz aktiviran venv) pokrenite:
```bash
python main.py
```

## Pregled podataka u InfluxDB
Podaci se mogu pregledati putem InfluxDB Web UI-a:
1. Otvorite `http://localhost:8086` u browseru.
2. Prijavite se sa kredencijalima:
   - **Korisničko ime:** `admin`
   - **Lozinka:** `adminpassword`
3. Idite na **Explore** (ikona grafikona sa leve strane).
4. Izaberite željeni buket (npr. `dht`, `pir`, `ultrasonic`) da biste videli prikupljene podatke.
5. InfluxDB token koji se koristi u aplikaciji je `iot_token_123`, a organizacija je `iot_org`.

## Pregled podataka u Grafana
Za naprednu vizuelizaciju podataka sa svih senzora i stanja aktuatora koristite Grafana dashboard:
1. Otvorite `http://localhost:3000` u browseru.
2. Prijavite se sa kredencijalima:
   - **Korisničko ime:** `admin`
   - **Lozinka:** `admin`
3. Sa leve strane izaberite **Dashboards**.
4. Otvorite **IoT System Dashboard**. Dashboard je unapred konfigurisan i automatski učitava podatke iz InfluxDB-a.

## Config
Konfiguracija uređaja vrši se kroz fajl `settings.json` (ili specifične fajlove poput `settings_P1.json`), gde se za svaki senzor i aktuator definišu pinovi i režim rada (simuliran ili realan).

## Uređaji
### Senzori
- **DS1** - Door Sensor
- **DPIR1** - Door Motion Sensor
- **DUS1** - Door Ultrasonic Sensor
- **DMS** - Door Membrane Switch
### Aktuatori
- **DL** - Door Light
- **DB** - Door Buzzer
