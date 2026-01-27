from core.mqtt_publisher import mqtt_publisher

class SensorBase:
    def __init__(self, code, cfg):
        self.code = code
        self.cfg = cfg

    def start(self, threads, stop_event):
        raise NotImplementedError


class ActuatorBase:
    def __init__(self, code, cfg):
        self.code = code
        self.cfg = cfg

    def handle(self, args):
        """args = lista tokena posle koda"""
        raise NotImplementedError

    def publish_status(self, value):
        data = {
            "measurement": "Actuator",
            "pi": self.cfg.get("pi", "unknown"),
            "device": self.cfg.get("name", "unknown"),
            "code": self.code,
            "simulated": self.cfg.get("simulated", False),
            "value": value
        }
        mqtt_publisher.publish_data("Actuator", data)