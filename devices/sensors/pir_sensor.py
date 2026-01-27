import threading
import time

from devices.base import SensorBase
from devices.gpio_adapter import GPIOAdapter
from simulators.pir_sim import run_pir_sim

from core.console import safe_print, print_prompt
from core.mqtt_publisher import mqtt_publisher
import settings

class PIRSensor(SensorBase):
    """ Passive Infrared Sensor """

    def start(self, threads, stop_event):
        delay = self.cfg.get("interval", 0.5)
        is_simulated = self.cfg.get("simulated", True)

        def callback(motion):
            ts = time.strftime("%H:%M:%S")
            safe_print(f"\n[{ts}] {self.code} motion={motion}")
            print_prompt()

            data = {
                "measurement": "PIR",
                "pi": settings.settings.get("PI", "unknown"),
                "device": self.cfg.get("name", self.code),
                "code": self.code,
                "value": motion,
                "simulated": is_simulated,
                "timestamp": time.time()
            }
            mqtt_publisher.publish_data("PIR", data)

        # simulated
        if self.cfg.get("simulated", True):
            t = threading.Thread(
                target=run_pir_sim,
                args=(delay, callback, stop_event),
                daemon=True
            )
            t.start()
            threads.append(t)
            return

        # real
        gpio = GPIOAdapter()
        pin = self.cfg["pin"]
        gpio.setup_in(pin)

        def loop():
            last = None
            while not stop_event.is_set():
                val = gpio.read(pin)
                if val != last:
                    last = val
                    callback(val)
                time.sleep(delay)

        t = threading.Thread(target=loop, daemon=True)
        t.start()
        threads.append(t)