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