import threading
import time
from devices.base import SensorBase
from devices.gpio_adapter import GPIOAdapter
from simulators.button_sim import run_button_sim
from core.console import safe_print, print_prompt
from core.mqtt_publisher import mqtt_publisher
import settings

class KitchenButton(SensorBase):
    """Simple kitchen button"""

    def start(self, threads, stop_event):
        delay = self.cfg.get("interval", 0.5)
        is_simulated = self.cfg.get("simulated", True)

        def callback(state):
            ts = time.strftime("%H:%M:%S")
            safe_print(f"\n[{ts}] {self.code} button={'PRESSED' if state else 'RELEASED'}")
            print_prompt()

            data = {
                "measurement": "Button",
                "pi": settings.settings.get("PI", "unknown"),
                "device": self.cfg.get("name", self.code),
                "code": self.code,
                "value": state,
                "simulated": is_simulated,
                "timestamp": time.time()
            }
            mqtt_publisher.publish_data("Button", data)

        if self.cfg.get("simulated", True):
            t = threading.Thread(target=run_button_sim, args=(delay, callback, stop_event), daemon=True)
            t.start()
            threads.append(t)
            return

        gpio = GPIOAdapter()
        pin = self.cfg["pin"]
        gpio.setup_in(pin, pull=self.cfg.get("pull", "UP"))

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