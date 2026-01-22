import time
import random


def run_dht_sim(interval, callback, stop_event):
    temp = 22.0 + random.uniform(-2, 2)
    humidity = 50.0 + random.uniform(-5, 5)

    while not stop_event.is_set():
        # realistic change
        temp += random.uniform(-0.3, 0.3)
        humidity += random.uniform(-0.5, 0.5)

        temp = max(15.0, min(30.0, temp))  # room temp
        humidity = max(30.0, min(70.0, humidity))  # normal humidity

        callback(temp, humidity)
        time.sleep(interval)