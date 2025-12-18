import threading
import time

from devices.base import SensorBase
from devices.gpio_adapter import GPIOAdapter
from simulators.pir_sim import run_pir_sim

from core.console import safe_print, print_prompt


class PIRSensor(SensorBase):
    def start(self, threads, stop_event):
        delay = self.cfg.get("interval", 0.5)

        def callback(motion):
            ts = time.strftime("%H:%M:%S")
            safe_print(f"\n[{ts}] {self.code} motion={motion}")
            print_prompt()

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