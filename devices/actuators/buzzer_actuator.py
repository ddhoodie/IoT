import time
from devices.base import ActuatorBase
from devices.gpio_adapter import GPIOAdapter

class BuzzerActuator(ActuatorBase):
    """Buzzer Control"""

    def __init__(self, code, cfg):
        super().__init__(code, cfg)
        self.gpio = GPIOAdapter()
        if not cfg.get("simulated", True):
            self.pin = cfg["pin"]
            self.gpio.setup_out(self.pin)
        else:
            self.pin = None

    def handle(self, args):
        if not args:
            raise ValueError("Usage: db on|off|beep <ms>")

        cmd = args[0].lower()
        if cmd in ("on", "off"):
            val = 1 if cmd == "on" else 0
            if self.pin is not None:
                self.gpio.write(self.pin, val)
            print(f"{self.code} -> {cmd}")
            self.publish_status(val)
            return

        if cmd == "beep":
            ms = int(args[1]) if len(args) > 1 else 200
            print(f"{self.code} -> beep {ms}ms")
            self.publish_status(1)
            if self.pin is not None:
                self.gpio.write(self.pin, 1)
                time.sleep(ms / 1000.0)
                self.gpio.write(self.pin, 0)
            self.publish_status(0)
            return

        raise ValueError("Usage: db on|off|beep <ms>")