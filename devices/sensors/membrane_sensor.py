import threading
import time

from devices.base import SensorBase
from devices.gpio_adapter import GPIOAdapter
from simulators.membrane_sim import run_membrane_sim

from core.console import safe_print, print_prompt  # <-- OVDE

class MembraneSensor(SensorBase):
    def start(self, threads, stop_event):
        delay = self.cfg.get("interval", 0.2)
        pins = self.cfg.get("pins", [])

        def callback(key_index):
            ts = time.strftime("%H:%M:%S")
            if key_index == -1:
                safe_print(f"\n[{ts}] {self.code} key=none")
            else:
                safe_print(f"\n[{ts}] {self.code} key={key_index}")
            print_prompt()

        # simulated
        if self.cfg.get("simulated", True):
            t = threading.Thread(
                target=run_membrane_sim,
                args=(delay, callback, stop_event, len(pins) or 4),
                daemon=True
            )
            t.start()
            threads.append(t)
            return

        # real
        gpio = GPIOAdapter()
        pull = self.cfg.get("pull", "UP")
        for p in pins:
            gpio.setup_in(p, pull=pull)

        def loop():
            last = None
            while not stop_event.is_set():
                pressed = -1
                for i, p in enumerate(pins):
                    val = gpio.read(p)
                    if val == 0:
                        pressed = i
                        break

                if pressed != last:
                    last = pressed
                    callback(pressed)

                time.sleep(delay)

        t = threading.Thread(target=loop, daemon=True)
        t.start()
        threads.append(t)
