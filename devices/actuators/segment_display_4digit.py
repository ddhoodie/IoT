import threading
import time
from devices.base import ActuatorBase


class SegmentDisplay4Digit(ActuatorBase):
    """4-Digit 7-Segment Display Timer"""

    def __init__(self, code, cfg):
        super().__init__(code, cfg)
        self.display = None
        self.current_value = "0000"
        self.timer_running = False
        self.timer_thread = None
        self.stop_timer = threading.Event()

        if not cfg.get("simulated", True):
            try:
                import board  # type: ignore
                from adafruit_ht16k33 import segments  # type: ignore
                i2c = board.I2C()
                self.display = segments.Seg7x4(i2c, address=cfg.get("address", 0x70))
                self.display.brightness = cfg.get("brightness", 1.0)
            except ImportError:
                print(f"adafruit_ht16k33 not installed, using simulation for {code}")
            except Exception as e:
                print(f"7-Segment display initialization failed: {e}")

    def _update_display(self, text):
        if self.display:
            self.display.print(text)
        self.current_value = text

    def _run_timer(self, seconds):
        remaining = seconds
        while remaining > 0 and not self.stop_timer.is_set():
            mins = remaining // 60
            secs = remaining % 60
            self._update_display(f"{mins:02d}{secs:02d}")
            print(f"{self.code} -> {mins:02d}:{secs:02d}")
            time.sleep(1)
            remaining -= 1

        self._update_display("0000")
        print(f"{self.code} -> Timer finished!")
        self.timer_running = False

    def handle(self, args):
        if not args:
            raise ValueError(
                f"Usage: {self.code.lower()} <number> | {self.code.lower()} timer <seconds> | {self.code.lower()} stop")

        cmd = args[0].lower()

        if cmd == "stop":
            if self.timer_running:
                self.stop_timer.set()
                if self.timer_thread:
                    self.timer_thread.join(timeout=2)
                self.timer_running = False
                print(f"{self.code} -> Timer stopped")
            else:
                print(f"{self.code} -> No timer running")
            return

        if cmd == "timer":
            if len(args) < 2:
                raise ValueError(f"Usage: {self.code.lower()} timer <seconds>")

            seconds = int(args[1])
            if self.timer_running:
                print(f"{self.code} -> Timer already running, stop it first")
                return

            self.stop_timer.clear()
            self.timer_running = True
            self.timer_thread = threading.Thread(target=self._run_timer, args=(seconds,), daemon=True)
            self.timer_thread.start()
            print(f"{self.code} -> Timer started: {seconds}s")
            return

        # Display number
        try:
            number = int(cmd)
            text = f"{number:04d}"
            self._update_display(text)
            print(f"{self.code} -> {text}")
        except ValueError:
            raise ValueError(f"Usage: {self.code.lower()} <number> | {self.code.lower()} timer <seconds>")