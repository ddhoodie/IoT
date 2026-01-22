from devices.base import ActuatorBase


class LCDActuator(ActuatorBase):
    """LCD Display (I2C)"""

    def __init__(self, code, cfg):
        super().__init__(code, cfg)
        self.lcd = None

        if not cfg.get("simulated", True):
            try:
                from RPLCD.i2c import CharLCD
                self.lcd = CharLCD(
                    'PCF8574',
                    cfg.get("address", 0x27),
                    cols=cfg.get("cols", 16),
                    rows=cfg.get("rows", 2)
                )
            except:
                print(f"LCD not available, using simulation for {code}")

    def handle(self, args):
        if not args:
            raise ValueError(f"Usage: {self.code.lower()} clear | {self.code.lower()} <text>")

        if args[0].lower() == "clear":
            if self.lcd:
                self.lcd.clear()
            print(f"{self.code} -> cleared")
            return

        text = " ".join(args)
        if self.lcd:
            self.lcd.clear()
            self.lcd.write_string(text[:32])  # Max 32 chars for 16x2

        print(f"{self.code} -> '{text}'")