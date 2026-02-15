import paho.mqtt.client as mqtt
import json
import time
import random

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

def publish(topic, data):
    print(f"Publishing to {topic}: {data}")
    client.publish(topic, json.dumps(data))

# Mock Sensors
sensors = [
    ("dht", {"measurement": "DHT", "value": {"temperature": 22.5, "humidity": 45.0}, "code": "DHT1"}),
    ("pir", {"measurement": "PIR", "value": 1, "code": "DPIR1"}),
    ("ultrasonic", {"measurement": "Ultrasonic", "value": 120.5, "code": "DUS1"}),
    ("gyroscope", {"measurement": "Gyroscope", "value": {"accel_x": 0.1, "accel_y": -0.2, "accel_z": 9.8, "gyro_x": 0.01, "gyro_y": 0.02, "gyro_z": 0.0}, "code": "GYR"}),
    ("ir", {"measurement": "IR", "value": 1, "code": "IR1"}),
    ("button", {"measurement": "Button", "value": 1, "code": "DS1"}),
    ("membrane", {"measurement": "Membrane", "value": "A", "code": "DMS"}),
    ("webcam", {"measurement": "Webcam", "value": {"event": "person_detected", "frame_id": 123, "confidence": 0.98}, "code": "WEBC"}),
]

# Mock Actuators
actuators = [
    ("actuator", {"measurement": "Actuator", "value": 1, "code": "DL"}),
    ("actuator", {"measurement": "Actuator", "value": {"r": 255, "g": 0, "b": 0}, "code": "BRGB"}),
    ("actuator", {"measurement": "Actuator", "value": "Hello World", "code": "LCD"}),
    ("actuator", {"measurement": "Actuator", "value": "1234", "code": "4SD"}),
]

print("Starting mock data publication...")
for topic, data in sensors + actuators:
    data["pi"] = "PI1"
    data["device"] = data["code"]
    data["simulated"] = True
    publish(topic, data)
    time.sleep(0.1)

client.disconnect()
print("Done.")
