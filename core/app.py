from settings import load_settings
from core.registry import SENSORS, ACTUATORS
import threading
from core.console import safe_print, console_lock

class App:
    def run(self):
        cfg = load_settings()
        devices_cfg = cfg.get("devices", {})

        stop_event = threading.Event()
        threads = []

        sensors = {}
        actuators = {}

        # init devices from config
        for code, dc in devices_cfg.items():
            if not dc.get("enabled", True):
                continue

            ucode = code.upper()
            if ucode in SENSORS:
                sensors[ucode] = SENSORS[ucode](ucode, dc)
            elif ucode in ACTUATORS:
                actuators[ucode] = ACTUATORS[ucode](ucode, dc)
            else:
                print("Unknown code in settings:", ucode)

        # start sensors
        for s in sensors.values():
            s.start(threads, stop_event)

        # console loop
        self.console_loop(actuators, stop_event)

        # stop
        stop_event.set()
        for t in threads:
            t.join(timeout=2)
        print("Bye.")

    def console_loop(self, actuators, stop_event):
        safe_print("\nAvailable actuators:")
        for code in actuators:
            safe_print(f"  {code.lower()}")
        safe_print("\nCommands: <actuator> <args> | help | status | exit\n")

        while not stop_event.is_set():
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not line:
                continue
            if line in ("exit", "quit"):
                break
            if line == "help":
                safe_print("Available commands:")
                safe_print("  dl on|off|toggle")
                safe_print("  db on|off|beep <ms>")
                safe_print("  brgb <r> <g> <b>")
                safe_print("  lcd <text> | lcd clear")
                safe_print("  4sd <number>")
                safe_print("  status | exit")
                continue

            if line == "status":
                safe_print(f"Running {len(actuators)} actuators")
                continue

            parts = line.split()
            code = parts[0].upper()
            args = parts[1:]

            if code not in actuators:
                safe_print(f"Unknown actuator: {code}")
                continue

            try:
                actuators[code].handle(args)
            except Exception as e:
                safe_print(f"Error: {e}")