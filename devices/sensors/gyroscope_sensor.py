import threading
import time
from devices.base import SensorBase
from simulators.gyroscope_sim import run_gyroscope_sim
from core.console import safe_print, print_prompt


class GyroscopeSensor(SensorBase):
    """Gyroscope and accelerator"""

    def start(self, threads, stop_event):
        interval = self.cfg.get("interval", 0.5)

        def callback(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z):
            ts = time.strftime("%H:%M:%S")
            safe_print(f"\n[{ts}] {self.code} accel=({accel_x:.2f},{accel_y:.2f},{accel_z:.2f}) "
                       f"gyro=({gyro_x:.2f},{gyro_y:.2f},{gyro_z:.2f})")
            print_prompt()

        if self.cfg.get("simulated", True):
            t = threading.Thread(
                target=run_gyroscope_sim,
                args=(interval, callback, stop_event),
                daemon=True
            )
            t.start()
            threads.append(t)
            return

        # Pravi MPU6050
        try:
            import smbus
            bus = smbus.SMBus(1)
            address = self.cfg.get("address", 0x68)

            # Inicijalizacija MPU6050
            bus.write_byte_data(address, 0x6B, 0)

            def read_word_2c(reg):
                high = bus.read_byte_data(address, reg)
                low = bus.read_byte_data(address, reg + 1)
                val = (high << 8) + low
                if val >= 0x8000:
                    return -((65535 - val) + 1)
                return val

            def loop():
                while not stop_event.is_set():
                    accel_x = read_word_2c(0x3B) / 16384.0
                    accel_y = read_word_2c(0x3D) / 16384.0
                    accel_z = read_word_2c(0x3F) / 16384.0

                    gyro_x = read_word_2c(0x43) / 131.0
                    gyro_y = read_word_2c(0x45) / 131.0
                    gyro_z = read_word_2c(0x47) / 131.0

                    callback(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)
                    time.sleep(interval)

            t = threading.Thread(target=loop, daemon=True)
            t.start()
            threads.append(t)
        except:
            safe_print(f"MPU6050 not available, falling back to simulation for {self.code}")
            t = threading.Thread(
                target=run_gyroscope_sim,
                args=(interval, callback, stop_event),
                daemon=True
            )
            t.start()
            threads.append(t)