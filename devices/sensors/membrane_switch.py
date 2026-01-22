import threading
import time
from devices.base import SensorBase
from devices.gpio_adapter import GPIOAdapter
from simulators.membrane_sim import run_membrane_sim
from core.console import safe_print, print_prompt


class MembraneSwitchSensor(SensorBase):
    """4x4 Membrane Matrix Keypad"""

    def start(self, threads, stop_event):
        interval = self.cfg.get("interval", 0.2)

        def callback(key):
            ts = time.strftime("%H:%M:%S")
            safe_print(f"\n[{ts}] {self.code} key_pressed='{key}'")
            print_prompt()

        if self.cfg.get("simulated", True):
            t = threading.Thread(
                target=run_membrane_sim,
                args=(interval, callback, stop_event),
                daemon=True
            )
            t.start()
            threads.append(t)
            return

        # Prava tastatura 4x4
        gpio = GPIOAdapter()
        pins = self.cfg["pins"]  # [row1, row2, row3, row4, col1, col2, col3, col4]

        row_pins = pins[:4]
        col_pins = pins[4:]

        for pin in row_pins:
            gpio.setup_out(pin)
        for pin in col_pins:
            gpio.setup_in(pin, pull="DOWN")

        keys = [
            ['1', '2', '3', 'A'],
            ['4', '5', '6', 'B'],
            ['7', '8', '9', 'C'],
            ['*', '0', '#', 'D']
        ]

        def scan_keypad():
            for i, row_pin in enumerate(row_pins):
                gpio.write(row_pin, 1)
                for j, col_pin in enumerate(col_pins):
                    if gpio.read(col_pin):
                        gpio.write(row_pin, 0)
                        return keys[i][j]
                gpio.write(row_pin, 0)
            return None

        def loop():
            last_key = None
            while not stop_event.is_set():
                key = scan_keypad()
                if key and key != last_key:
                    callback(key)
                last_key = key
                time.sleep(interval)

        t = threading.Thread(target=loop, daemon=True)
        t.start()
        threads.append(t)