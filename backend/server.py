from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import threading
import time

app = Flask(__name__)

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "#"

# Globalni MQTT klijent za slanje komandi
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

def send_command(pi, device, command, *args):
    topic = f"smart_home/{pi.lower()}/command/{device.upper()}"
    payload = f"{command} {' '.join(map(str, args))}".strip()
    mqtt_client.publish(topic, payload)
    print(f"Sent MQTT command to {topic}: {payload}")

INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "iot_token_123"
INFLUXDB_ORG = "iot_org"

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)
buckets_api = client.buckets_api()

existing_buckets = set()

def ensure_bucket_exists(bucket_name):
    if bucket_name in existing_buckets:
        return

    try:
        print(f"Checking bucket: {bucket_name}")
        bucket = buckets_api.find_bucket_by_name(bucket_name)
        if not bucket:
            print(f"Bucket {bucket_name} not found, creating...")
            buckets_api.create_bucket(bucket_name=bucket_name, org=INFLUXDB_ORG)
            print(f"Created bucket: {bucket_name}")
        existing_buckets.add(bucket_name)
    except Exception as e:
        print(f"Error ensuring bucket {bucket_name} exists: {e}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"MQTT Server: Connected to broker, result code {rc}")
        client.subscribe(MQTT_TOPIC)
        print(f"MQTT Server: Subscribed to {MQTT_TOPIC}")
    else:
        print(f"MQTT Server: Failed to connect, result code {rc}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"MQTT Server: Unexpectedly disconnected from broker, code {rc}")
    else:
        print(f"MQTT Server: Disconnected from broker")

def on_message(client, userdata, msg):
    # topic parts: smart_home/pi1/DHT
    if "/command/" in msg.topic:
        return
    
    try:
        payload = json.loads(msg.payload.decode())
        if isinstance(payload, list):
            for data in payload:
                update_device_state(data)
                save_to_influx(data)
                process_sensor_data(data)
        else:
            update_device_state(payload)
            save_to_influx(payload)
            process_sensor_data(payload)
    except Exception as e:
        print(f"Error processing message: {e}")

def process_sensor_data(data):
    code = data.get("code")
    val = data.get("value")
    
    # DL1 logika (DPIR1)
    if code == "DPIR1" and val:
        send_command("pi1", "DL", "on")
        threading.Timer(10.0, lambda: send_command("pi1", "DL", "off")).start()

    # People count (PIR + DUS)
    handle_people_count(data)

    # Alarm - DS1/DS2 > 5s
    handle_door_sensors(data)

    # Alarm - RPIR1-3
    if code in ["RPIR1", "RPIR2", "RPIR3"] and val:
        if STATE["people_count"] == 0:
            trigger_alarm(f"motion_detected_by_{code}_but_home_empty")

    # Alarm - GSG
    if code == "GYR":
        # val je {accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z}
        accel = val.get("accel_x", 0)**2 + val.get("accel_y", 0)**2 + val.get("accel_z", 0)**2
        if accel > 4.0: # arbitrary threshold for "significant movement"
            trigger_alarm("gsg_significant_movement")

    # Alarm - PIN na DMS
    if code == "DMS" and val:
        handle_dms_input(val)

    # RGB - IR kontrola
    if code == "IR" and val:
        handle_ir_control(val)

    # BTN - Kuhinjsko dugme
    if code == "BTN" and val:
        handle_btn_input()

def handle_btn_input():
    t = STATE["timer"]
    if t["finished"]:
        t["finished"] = False
        print("Timer flashing stopped via BTN")
        touch()
    else:
        # Dodaj N sekundi
        t["seconds_left"] += int(t["add_n_seconds"])
        t["running"] = t["seconds_left"] > 0
        send_command("pi2", "4SD", "stop")
        send_command("pi2", "4SD", "timer", t["seconds_left"])
        print(f"Added {t['add_n_seconds']}s to timer via BTN")
        touch()

def trigger_alarm(reason):
    if not STATE["alarm"]:
        STATE["alarm"] = True
        STATE["last_alarm_reason"] = reason
        send_command("pi1", "DB", "on")
        print(f"ALARM TRIGGERED: {reason}")
        save_alarm_event(reason, "entered")
        touch()

def save_alarm_event(reason, state):
    # state: "entered" ili "exited"
    try:
        point = Point("AlarmEvent") \
            .tag("reason", reason) \
            .tag("state", state) \
            .field("active", 1 if state == "entered" else 0)
        
        ensure_bucket_exists("system")
        write_api.write(bucket="system", record=point)
    except Exception as e:
        print(f"Error saving alarm event to InfluxDB: {e}")

DUS_HISTORY = {"DUS1": [], "DUS2": []}
def handle_people_count(data):
    code = data.get("code")
    val = data.get("value")
    if code in ["DUS1", "DUS2"]:
        hist = DUS_HISTORY[code]
        hist.append((time.time(), val))
        if len(hist) > 10: hist.pop(0)
    
    if code in ["DPIR1", "DPIR2"] and val:
        # Proveri distancu u poslednjih par sekundi
        dus_code = "DUS1" if code == "DPIR1" else "DUS2"
        pi_id = "pi1" if code == "DPIR1" else "pi2"
        hist = DUS_HISTORY[dus_code]
        if len(hist) >= 2:
            # Ako se distanca smanjivala -> ulazak
            # Ako se distanca povećavala -> izlazak
            d1 = hist[-2][1]
            d2 = hist[-1][1]
            if d2 < d1: # približava se senzoru (ulazi u domet/objekat)
                STATE["people_count"] += 1
                print(f"Person entered via {code}")
            else:
                STATE["people_count"] = max(0, STATE["people_count"] - 1)
                print(f"Person exited via {code}")
            touch()

DOOR_OPEN_START = {"DS1": None, "DS2": None}
def handle_door_sensors(data):
    code = data.get("code")
    val = data.get("value")
    if code in ["DS1", "DS2"]:
        if val == 1: # Otključana/otvorena (zavisi od senzora, obično 1 je open)
            if DOOR_OPEN_START[code] is None:
                DOOR_OPEN_START[code] = time.time()
            elif time.time() - DOOR_OPEN_START[code] > 5:
                trigger_alarm(f"door_{code}_open_too_long")
        else:
            DOOR_OPEN_START[code] = None
            # Ako je alarm bio zbog ovoga, ne gasimo ga automatski po specifikaciji, 
            # specifikacija kaže "dok se stanje DS-a ne promeni" -> možda ipak gasimo?
            # "uključiti ALARM dok se stanje DS-a ne promeni"
            if STATE["alarm"] and STATE["last_alarm_reason"] == f"door_{code}_open_too_long":
                STATE["alarm"] = False
                STATE["last_alarm_reason"] = ""
                send_command("pi1", "DB", "off")
                touch()
        
        # Ako je sistem aktivan, alarm odmah (skoro)
        if STATE["armed"] and val == 1:
             # Spec: "uključiti ALARM ukoliko se ne detektuje ispravno unet PIN na DMS komponenti"
             # Ovo podrazumeva mali delay ili odmah? Obično ima delay za ulazak.
             threading.Timer(10.0, lambda: check_alarm_after_delay(code)).start()

def check_alarm_after_delay(code):
    if STATE["armed"] and not STATE["alarm"]:
        # Ako je i dalje armed (nije unet PIN), pali alarm
        trigger_alarm(f"unauthorized_entry_{code}")

DMS_BUFFER = ""
def handle_dms_input(key):
    global DMS_BUFFER
    if key.isdigit():
        DMS_BUFFER += key
        if len(DMS_BUFFER) == 4:
            if DMS_BUFFER == PIN_CODE:
                if STATE["alarm"]:
                    save_alarm_event(STATE["last_alarm_reason"], "exited")
                    STATE["alarm"] = False
                    STATE["last_alarm_reason"] = ""
                    send_command("pi1", "DB", "off")
                    print("Alarm deactivated via DMS")
                
                if STATE["armed"]:
                    STATE["armed"] = False
                    print("System disarmed via DMS")
                else:
                    # Aktivacija sa 10s delay
                    print("System arming in 10s...")
                    threading.Timer(10.0, lambda: set_armed(True)).start()
                touch()
            else:
                print("Invalid PIN on DMS")
            DMS_BUFFER = ""
    elif key == "*": DMS_BUFFER = ""

def set_armed(val):
    STATE["armed"] = val
    touch()
    print(f"System armed: {val}")

def handle_ir_control(key):
    # Mapiranje IR tastera na boje
    colors = {
        "1": (255, 0, 0), "2": (0, 255, 0), "3": (0, 0, 255),
        "4": (255, 255, 0), "5": (255, 0, 255), "6": (0, 255, 255),
        "0": (0, 0, 0)
    }
    if key in colors:
        r, g, b = colors[key]
        STATE["rgb"] = {"on": key != "0", "r": r, "g": g, "b": b}
        send_command("pi3", "BRGB", r, g, b)
        touch()

def update_device_state(data):
    try:
        code = data.get("code")
        if code:
            STATE["devices"][code] = {
                "value": data.get("value"),
                "timestamp": data.get("timestamp") or time.time(),
                "measurement": data.get("measurement"),
                "device": data.get("device")
            }
            STATE["last_update_ts"] = time.time()
    except Exception as e:
        print(f"Error updating device state: {e}")

def save_to_influx(data):
    try:
        sensor_type = data.get("measurement", "Unknown")
        bucket = sensor_type.lower()

        point = Point(sensor_type) \
            .tag("pi", data.get("pi", "unknown")) \
            .tag("device", data.get("device", "unknown")) \
            .tag("code", data.get("code", "unknown")) \
            .tag("simulated", str(data.get("simulated", False)))

        values = data.get("value")
        if isinstance(values, dict):
            for key, val in values.items():
                if val is not None:
                    point.field(key, val)
        elif values is not None:
            point.field("value", values)
        else:
            print(f"MQTT Server: No values to save for {data.get('code')}")
            return

        ensure_bucket_exists(bucket)
        write_api.write(bucket=bucket, record=point)
        print(f"Saved to InfluxDB bucket {bucket}: {data.get('code')}")
    except Exception as e:
        print(f"Error saving to InfluxDB: {e}")
        print(f"Failed data: {data}")

def start_mqtt():
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print(f"MQTT Server: Started loop and connecting to {MQTT_BROKER}:{MQTT_PORT}...")
    except Exception as e:
        print(f"MQTT Server: Error connecting to broker: {e}")

# -------------------------------------------------------
# WEB UI + MOCK API (za front prvo, kasnije povezujemo)
# -------------------------------------------------------

STATE = {
    "armed": False,
    "alarm": False,
    "people_count": 0,
    "last_alarm_reason": "",
    "rgb": {"on": False, "r": 255, "g": 0, "b": 0},
    "timer": {
        "seconds_left": 0,
        "set_seconds": 0,
        "add_n_seconds": 10,
        "running": False,
        "finished": False
    },
    "last_update_ts": time.time(),
    "devices": {}
}

PIN_CODE = "1234"  # za demo; posle prebaci u settings

def touch():
    STATE["last_update_ts"] = time.time()
    save_state_to_influx()

def save_state_to_influx():
    try:
        point = Point("SystemState") \
            .field("armed", int(STATE["armed"])) \
            .field("alarm", int(STATE["alarm"])) \
            .field("people_count", STATE["people_count"]) \
            .field("timer_seconds", STATE["timer"]["seconds_left"])

        ensure_bucket_exists("system")
        write_api.write(bucket="system", record=point)
    except Exception as e:
        print(f"Error saving system state to InfluxDB: {e}")

def require_pin(data) -> bool:
    return (data or {}).get("pin") == PIN_CODE

@app.route("/")
def index():
    # Renderuje templates/index.html
    return render_template("index.html")

@app.route("/api/state", methods=["GET"])
def api_state():
    return jsonify(STATE)

@app.route("/api/alarm/arm", methods=["POST"])
def api_arm():
    data = request.get_json(silent=True) or {}
    if not require_pin(data):
        return jsonify({"ok": False, "error": "Invalid PIN"}), 401
    # Aktivacija sa 10s delay po specifikaciji
    threading.Timer(10.0, lambda: set_armed(True)).start()
    return jsonify({"ok": True, "message": "Arming in 10s"})

@app.route("/api/alarm/disarm", methods=["POST"])
def api_disarm():
    data = request.get_json(silent=True) or {}
    if not require_pin(data):
        return jsonify({"ok": False, "error": "Invalid PIN"}), 401
    if STATE["alarm"]:
        save_alarm_event(STATE["last_alarm_reason"], "exited")
    STATE["armed"] = False
    STATE["alarm"] = False
    STATE["last_alarm_reason"] = ""
    send_command("pi1", "DB", "off")
    touch()
    return jsonify({"ok": True, "state": STATE})

@app.route("/api/alarm/trigger", methods=["POST"])
def api_trigger_alarm():
    # Namerno bez PIN-a da možeš da demonstriraš 1 klikom
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "manual_trigger")
    STATE["alarm"] = True
    STATE["last_alarm_reason"] = reason
    touch()
    return jsonify({"ok": True, "state": STATE})

@app.route("/api/alarm/stop", methods=["POST"])
def api_stop_alarm():
    data = request.get_json(silent=True) or {}
    if not require_pin(data):
        return jsonify({"ok": False, "error": "Invalid PIN"}), 401
    if STATE["alarm"]:
        save_alarm_event(STATE["last_alarm_reason"], "exited")
    STATE["alarm"] = False
    STATE["last_alarm_reason"] = ""
    send_command("pi1", "DB", "off")
    touch()
    return jsonify({"ok": True, "state": STATE})

@app.route("/api/people", methods=["POST"])
def api_people():
    data = request.get_json(silent=True) or {}
    delta = int(data.get("delta", 0))
    STATE["people_count"] = max(0, STATE["people_count"] + delta)
    touch()
    return jsonify({"ok": True, "state": STATE})

@app.route("/api/rgb", methods=["POST"])
def api_rgb():
    data = request.get_json(silent=True) or {}
    rgb = STATE["rgb"]

    if "on" in data:
        rgb["on"] = bool(data["on"])

    for k in ("r", "g", "b"):
        if k in data:
            rgb[k] = max(0, min(255, int(data[k])))

    send_command("pi3", "BRGB", rgb["r"], rgb["g"], rgb["b"] if rgb["on"] else 0)
    touch()
    return jsonify({"ok": True, "state": STATE})

@app.route("/api/timer/set", methods=["POST"])
def api_timer_set():
    data = request.get_json(silent=True) or {}
    seconds = max(0, int(data.get("seconds", 0)))

    t = STATE["timer"]
    t["set_seconds"] = seconds
    t["seconds_left"] = seconds
    t["running"] = seconds > 0
    t["finished"] = False
    
    send_command("pi2", "4SD", "timer", seconds)
    touch()
    return jsonify({"ok": True, "state": STATE})

@app.route("/api/timer/add_config", methods=["POST"])
def api_timer_add_config():
    data = request.get_json(silent=True) or {}
    n = max(1, int(data.get("n_seconds", 1)))
    STATE["timer"]["add_n_seconds"] = n
    touch()
    return jsonify({"ok": True, "state": STATE})

@app.route("/api/timer/add", methods=["POST"])
def api_timer_add():
    t = STATE["timer"]
    t["seconds_left"] += int(t["add_n_seconds"])
    t["running"] = t["seconds_left"] > 0
    t["finished"] = False
    
    send_command("pi2", "4SD", "stop")
    send_command("pi2", "4SD", "timer", t["seconds_left"])
    touch()
    return jsonify({"ok": True, "state": STATE})

def lcd_loop():
    while True:
        dhts = ["DHT1", "DHT2", "DHT3"]
        for dht_code in dhts:
            if dht_code in STATE["devices"]:
                d = STATE["devices"][dht_code]
                val = d["value"]
                if isinstance(val, dict):
                    text = f"{dht_code}: {val.get('temp', 0)}C {val.get('hum', 0)}%"
                    send_command("pi3", "LCD", text)
            time.sleep(5)

def buzzer_loop():
    # Treperenje 4SD i zvuk kad tajmer istekne
    # Spec: "Kada istekne vreme na štoperici, potrebno je da 4SD treperi sa 00:00 na prikazu"
    # To radimo na frontu/u serveru? 4SD simulator ne podržava treperenje direktno.
    # Možemo slati naizmenično 0000 i prazno.
    is_on = True
    while True:
        if STATE["timer"]["finished"]:
            if is_on:
                send_command("pi2", "4SD", "0000")
            else:
                send_command("pi2", "4SD", "    ")
            is_on = not is_on
        time.sleep(0.5)

def timer_loop():
    while True:
        time.sleep(1)
        t = STATE["timer"]
        if t["running"] and t["seconds_left"] > 0:
            t["seconds_left"] -= 1
            touch()
            if t["seconds_left"] <= 0:
                t["seconds_left"] = 0
                t["running"] = False
                t["finished"] = True
                touch()

if __name__ == "__main__":
    start_mqtt()

    threading.Thread(target=timer_loop, daemon=True).start()
    threading.Thread(target=lcd_loop, daemon=True).start()
    threading.Thread(target=buzzer_loop, daemon=True).start()

    app.run(host="0.0.0.0", port=5000, debug=True)
