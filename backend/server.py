from flask import Flask
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import threading

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
    # print(f"MQTT Server: Payload: {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())
        if isinstance(payload, list):
            print(f"MQTT Server: Processing batch of {len(payload)} items")
            for data in payload:
                save_to_influx(data)
        else:
            save_to_influx(payload)
    except Exception as e:
        print(f"Error processing message: {e}")

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

@app.route('/')
def index():
    return "IoT Backend is running."

if __name__ == '__main__':
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    app.run(host='0.0.0.0', port=5000)
