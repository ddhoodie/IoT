from devices.base import ActuatorBase
from devices.gpio_adapter import GPIOAdapter


class RGBActuator(ActuatorBase):
    """RGB LED Control"""

    def __init__(self, code, cfg):
        super().__init__(code, cfg)
        self.gpio = GPIOAdapter()
        if not cfg.get("simulated", True):
            self.r_pin = cfg["r_pin"]
            self.g_pin = cfg["g_pin"]
            self.b_pin = cfg["b_pin"]
            self.gpio.setup_out(self.r_pin)
            self.gpio.setup_out(self.g_pin)
            self.gpio.setup_out(self.b_pin)
        else:
            self.r_pin = self.g_pin = self.b_pin = None

    def handle(self, args):
        if not args:
            raise ValueError(f"Usage: {self.code.lower()} <color> | {self.code.lower()} <r> <g> <b>")

        if len(args) == 1:
            # Predefined colors
            color = args[0].lower()
            colors = {
                "red": (1, 0, 0),
                "green": (0, 1, 0),
                "blue": (0, 0, 1),
                "yellow": (1, 1, 0),
                "cyan": (0, 1, 1),
                "magenta": (1, 0, 1),
                "white": (1, 1, 1),
                "off": (0, 0, 0)
            }
            if color not in colors:
                raise ValueError(f"Unknown color. Available: {', '.join(colors.keys())}")
            r, g, b = colors[color]
        elif len(args) == 3:
            # RGB values (0-255 or 0-1)
            r, g, b = [int(x) for x in args]
            if all(0 <= x <= 1 for x in [r, g, b]):
                pass  # Already 0-1
            elif all(0 <= x <= 255 for x in [r, g, b]):
                r, g, b = r / 255, g / 255, b / 255
            else:
                raise ValueError("RGB values must be 0-1 or 0-255")
        else:
            raise ValueError(f"Usage: {self.code.lower()} <color> | {self.code.lower()} <r> <g> <b>")

        if self.r_pin is not None:
            self.gpio.write(self.r_pin, r)
            self.gpio.write(self.g_pin, g)
            self.gpio.write(self.b_pin, b)

        print(f"{self.code} -> RGB({r},{g},{b})")