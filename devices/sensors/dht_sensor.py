import threading
import time
from devices.base import SensorBase
from devices.gpio_adapter import GPIOAdapter
from simulators.dht_sim import run_dht_sim
from core.console import safe_print, print_prompt


class DHTSensor(SensorBase):
    """Temperature & Humidity Sensor"""

    def start(self, threads, stop_event):
        interval = self.cfg.get("interval", 2.0)
        sensor_type = self.cfg.get("type", "DHT11")  # DHT11 ili DHT22

        def callback(temp, humidity):
            ts = time.strftime("%H:%M:%S")
            safe_print(f"\n[{ts}] {self.code} temp={temp:.1f}°C humidity={humidity:.1f}%")
            print_prompt()

        if self.cfg.get("simulated", True):
            # Simulacija
            t = threading.Thread(
                target=run_dht_sim,
                args=(interval, callback, stop_event),
                daemon=True
            )
            t.start()
            threads.append(t)
            return

        # Pravi DHT sensor
        try:
            import Adafruit_DHT
            pin = self.cfg["pin"]
            sensor = Adafruit_DHT.DHT11 if sensor_type == "DHT11" else Adafruit_DHT.DHT22

            def loop():
                while not stop_event.is_set():
                    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
                    if humidity is not None and temperature is not None:
                        callback(temperature, humidity)
                    time.sleep(interval)

            t = threading.Thread(target=loop, daemon=True)
            t.start()
            threads.append(t)
        except ImportError:
            safe_print(f"⚠️  Adafruit_DHT not installed, falling back to simulation for {self.code}")
            t = threading.Thread(
                target=run_dht_sim,
                args=(interval, callback, stop_event),
                daemon=True
            )
            t.start()
            threads.append(t)