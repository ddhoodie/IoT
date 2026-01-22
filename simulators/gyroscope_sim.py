import time
import random


def run_gyroscope_sim(interval, callback, stop_event):
    accel_x = random.uniform(-0.1, 0.1)
    accel_y = random.uniform(-0.1, 0.1)
    accel_z = 1.0 + random.uniform(-0.05, 0.05)  # Gravitacija

    gyro_x = random.uniform(-2, 2)
    gyro_y = random.uniform(-2, 2)
    gyro_z = random.uniform(-2, 2)

    while not stop_event.is_set():
        if random.random() < 0.1:
            # random movement
            accel_x += random.uniform(-0.5, 0.5)
            accel_y += random.uniform(-0.5, 0.5)
            accel_z += random.uniform(-0.2, 0.2)

            gyro_x += random.uniform(-20, 20)
            gyro_y += random.uniform(-20, 20)
            gyro_z += random.uniform(-20, 20)
        else:
            # going back
            accel_x *= 0.95
            accel_y *= 0.95
            accel_z = accel_z * 0.95 + 1.0 * 0.05  # Vraća se ka 1g

            gyro_x *= 0.9
            gyro_y *= 0.9
            gyro_z *= 0.9

        # noise
        accel_x += random.uniform(-0.02, 0.02)
        accel_y += random.uniform(-0.02, 0.02)
        accel_z += random.uniform(-0.02, 0.02)

        gyro_x += random.uniform(-0.5, 0.5)
        gyro_y += random.uniform(-0.5, 0.5)
        gyro_z += random.uniform(-0.5, 0.5)

        accel_x = max(-2.0, min(2.0, accel_x))
        accel_y = max(-2.0, min(2.0, accel_y))
        accel_z = max(-2.0, min(2.0, accel_z))

        gyro_x = max(-250, min(250, gyro_x))
        gyro_y = max(-250, min(250, gyro_y))
        gyro_z = max(-250, min(250, gyro_z))

        callback(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)
        time.sleep(interval)