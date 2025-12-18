import threading
import time

from devices.base import SensorBase
from simulators.ultrasonic_sim import run_ultrasonic_sim

from core.console import safe_print, print_prompt


class UltrasonicSensor(SensorBase):
    def start(self, threads, stop_event):
        delay = self.cfg.get("interval", 1)

        def callback(distance_cm):
            ts = time.strftime("%H:%M:%S")
            safe_print(f"\n[{ts}] {self.code} distance_cm={distance_cm:.1f}")
            print_prompt()

        if self.cfg.get("simulated", True):
            t = threading.Thread(
                target=run_ultrasonic_sim,
                args=(delay, callback, stop_event),
                daemon=True
            )
            t.start()
            threads.append(t)
            return

        raise NotImplementedError("Real ultrasonic not implemented yet. Set simulated=true.")
