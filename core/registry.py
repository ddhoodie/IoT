from devices.sensors.button_sensor import ButtonSensor
from devices.sensors.dht_sensor import DHTSensor
from devices.sensors.pir_sensor import PIRSensor
from devices.sensors.ultrasonic_sensor import UltrasonicSensor
from devices.sensors.ir_sensor import IRSensor
from devices.sensors.gyroscope_sensor import GyroscopeSensor
from devices.sensors.membrane_switch import MembraneSwitchSensor
from devices.sensors.kitchen_button import KitchenButton

from devices.actuators.buzzer_actuator import BuzzerActuator
from devices.actuators.led_actuator import LEDActuator
from devices.actuators.rgb_actuator import RGBActuator
from devices.actuators.lcd_actuator import LCDActuator
from devices.actuators.segment_display_4digit import SegmentDisplay4Digit
from devices.sensors.webcam_sensor import WebcamSensor

SENSORS = {
    "DS1": ButtonSensor,
    "DS2": ButtonSensor,
    "DHT1": DHTSensor,
    "DHT2": DHTSensor,
    "DHT3": DHTSensor,
    "DPIR1": PIRSensor,
    "DPIR2": PIRSensor,
    "DPIR3": PIRSensor,
    "DUS1": UltrasonicSensor,
    "DUS2": UltrasonicSensor,
    "IR": IRSensor,
    "GYR": GyroscopeSensor,
    "DMS": MembraneSwitchSensor,
    "BTN": KitchenButton,
    "WEBC": WebcamSensor,
}

ACTUATORS = {
    "DB": BuzzerActuator,
    "DL": LEDActuator,
    "BRGB": RGBActuator,
    "LCD": LCDActuator,
    "4SD": SegmentDisplay4Digit,
}