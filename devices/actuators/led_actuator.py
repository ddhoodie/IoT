from devices.base import ActuatorBase
from devices.gpio_adapter import GPIOAdapter


class LEDActuator(ActuatorBase):
    """LED Control"""

    def __init__(self, code, cfg):
        super().__init__(code, cfg)
        self.state = 0
        self.gpio = GPIOAdapter()
        if not cfg.get("simulated", True):
            self.pin = cfg["pin"]
            self.gpio.setup_out(self.pin)
        else:
            self.pin = None

    def handle(self, args):
        if not args:
            raise ValueError("Usage: dl on|off|toggle")

        cmd = args[0].lower()
        if cmd == "on":
            self.state = 1
        elif cmd == "off":
            self.state = 0
        elif cmd == "toggle":
            self.state = 1 - self.state
        else:
            raise ValueError("Usage: dl on|off|toggle")

        if self.pin is not None:
            self.gpio.write(self.pin, self.state)

        print(f"{self.code} -> {self.state}")
        self.publish_status(self.state)
