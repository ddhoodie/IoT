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
    print(f"MQTT Server: Received message on topic {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode())
        if isinstance(payload, list):
            print(f"MQTT Server: Processing batch of {len(payload)} items")
            for data in payload:
                update_device_state(data)
                save_to_influx(data)
        else:
            update_device_state(payload)
            save_to_influx(payload)
    except Exception as e:
        print(f"Error processing message: {e}")

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
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

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
    STATE["armed"] = True
    touch()
    return jsonify({"ok": True, "state": STATE})

@app.route("/api/alarm/disarm", methods=["POST"])
def api_disarm():
    data = request.get_json(silent=True) or {}
    if not require_pin(data):
        return jsonify({"ok": False, "error": "Invalid PIN"}), 401
    STATE["armed"] = False
    STATE["alarm"] = False
    STATE["last_alarm_reason"] = ""
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
    STATE["alarm"] = False
    STATE["last_alarm_reason"] = ""
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
    touch()
    return jsonify({"ok": True, "state": STATE})

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
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()

    threading.Thread(target=timer_loop, daemon=True).start()

    app.run(host="0.0.0.0", port=5000, debug=True)
