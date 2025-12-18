from devices.sensors.button_sensor import ButtonSensor
from devices.sensors.pir_sensor import PIRSensor
from devices.sensors.ultrasonic_sensor import UltrasonicSensor
from devices.sensors.membrane_sensor import MembraneSensor

from devices.actuators.led_actuator import LedActuator
from devices.actuators.buzzer_actuator import BuzzerActuator

SENSORS = {
    "DS1": ButtonSensor,
    "DPIR1": PIRSensor,
    "DUS1": UltrasonicSensor,
    "DMS": MembraneSensor
}

ACTUATORS = {
    "DL": LedActuator,
    "DB": BuzzerActuator
}