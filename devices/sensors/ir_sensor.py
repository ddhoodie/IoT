import threading
import time
from devices.base import SensorBase
from devices.gpio_adapter import GPIOAdapter
from simulators.ir_sim import run_ir_sim
from core.console import safe_print, print_prompt


class IRSensor(SensorBase):
    """Infrared Obstacle Detection Sensor"""

    def start(self, threads, stop_event):
        interval = self.cfg.get("interval", 0.5)

        def callback(detected):
            ts = time.strftime("%H:%M:%S")
            status = "OBJECT DETECTED" if detected else "clear"
            safe_print(f"\n[{ts}] {self.code} {status}")
            print_prompt()

        if self.cfg.get("simulated", True):
            t = threading.Thread(
                target=run_ir_sim,
                args=(interval, callback, stop_event),
                daemon=True
            )
            t.start()
            threads.append(t)
            return

        # Pravi IR sensor
        gpio = GPIOAdapter()
        pin = self.cfg["pin"]
        gpio.setup_in(pin)

        def loop():
            last_state = None
            while not stop_event.is_set():
                state = gpio.read(pin)
                if state != last_state:
                    last_state = state
                    callback(bool(state))
                time.sleep(interval)

        t = threading.Thread(target=loop, daemon=True)
        t.start()
        threads.append(t)