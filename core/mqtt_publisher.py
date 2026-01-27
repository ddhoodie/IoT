import json
import threading
import time
from queue import Queue
import paho.mqtt.client as mqtt

class MqttPublisher:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MqttPublisher, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.host = "localhost"
        self.port = 1883
        self.base_topic = "smart_home"
        self.queues = {} # sensor_type -> Queue
        self.threads = []
        self.stop_event = threading.Event()
        self.connected = False
        self._initialized = True

    def setup(self, settings):
        mqtt_cfg = settings.get("mqtt", {})
        self.host = mqtt_cfg.get("host", "localhost")
        self.port = mqtt_cfg.get("port", 1883)
        self.base_topic = mqtt_cfg.get("topic", "smart_home/pi")
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print(f"MQTT Publisher: Connected to {self.host}:{self.port}")
                self.connected = True
            else:
                print(f"MQTT Publisher: Failed to connect, return code {rc}")

        def on_disconnect(client, userdata, rc):
            self.connected = False
            if rc != 0:
                print(f"MQTT Publisher: Unexpectedly disconnected from broker, code {rc}")
            else:
                print(f"MQTT Publisher: Disconnected from broker")

        def on_publish(client, userdata, mid):
            # print(f"MQTT Publisher: Message {mid} published.")
            pass

        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.on_publish = on_publish
        
        try:
            # Reconnect automatically if loop_start is already running
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
            print(f"MQTT Publisher: Started loop and connecting to {self.host}:{self.port}...")
        except Exception as e:
            print(f"MQTT Publisher: Error connecting to broker: {e}")

    def publish_data(self, sensor_type, data):
        if sensor_type not in self.queues:
            with self._lock:
                if sensor_type not in self.queues:
                    queue = Queue()
                    self.queues[sensor_type] = queue
                    t = threading.Thread(target=self._batch_worker, args=(sensor_type, queue), daemon=True)
                    t.start()
                    self.threads.append(t)
        
        self.queues[sensor_type].put(data)

    def _batch_worker(self, sensor_type, queue):
        batch = []
        last_publish = time.time()
        batch_size = 1
        timeout = 1 # seconds

        while not self.stop_event.is_set():
            try:
                # Wait for data with timeout to allow periodic flushing
                # If disconnected, wait longer to avoid busy loop and spamming logs
                wait_time = 5 if not self.connected else 1
                item = queue.get(timeout=wait_time)
                batch.append(item)
                queue.task_done()
            except:
                pass # timeout reached

            now = time.time()
            if len(batch) >= batch_size or (len(batch) > 0 and now - last_publish > timeout):
                self._flush_batch(sensor_type, batch)
                batch = []
                last_publish = now

    def _flush_batch(self, sensor_type, batch):
        topic = f"{self.base_topic}/{sensor_type}"
        payload = json.dumps(batch)

        # Non-blocking connection check
        if not self.connected:
            print(f"MQTT Publisher: Not connected, cannot publish to {topic}. Data will be lost (batch size {len(batch)}).")
            # Try to reconnect if loop is not running or connection lost
            return

        print(f"MQTT Publisher: Publishing {len(batch)} items to {topic}")
        try:
            res = self.client.publish(topic, payload)
            if res.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"MQTT Publisher: Error calling publish, code {res.rc}")
                if res.rc == mqtt.MQTT_ERR_NO_CONN:
                    self.connected = False
            # else:
            #    print(f"MQTT Publisher: Publish call returned SUCCESS")
        except Exception as e:
            print(f"MQTT Publisher: Exception during publish: {e}")
            self.connected = False

    def stop(self):
        self.stop_event.set()
        self.client.loop_stop()
        self.client.disconnect()

mqtt_publisher = MqttPublisher()
