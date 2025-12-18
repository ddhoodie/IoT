class GPIOAdapter:
    def __init__(self):
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.is_real = True
            self.GPIO.setmode(GPIO.BCM)
            self.GPIO.setwarnings(False)
        except Exception:
            self.GPIO = None
            self.is_real = False

    def setup_in(self, pin, pull=None):
        if not self.is_real:
            return
        if pull == "UP":
            self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        elif pull == "DOWN":
            self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_DOWN)
        else:
            self.GPIO.setup(pin, self.GPIO.IN)

    def setup_out(self, pin):
        if not self.is_real:
            return
        self.GPIO.setup(pin, self.GPIO.OUT)

    def read(self, pin):
        if not self.is_real:
            return 0
        return self.GPIO.input(pin)

    def write(self, pin, value):
        if not self.is_real:
            return
        self.GPIO.output(pin, 1 if value else 0)

    def cleanup(self):
        if self.is_real:
            self.GPIO.cleanup()