import time
import random


def run_membrane_sim(interval, callback, stop_event):
    keys = [
        '1', '2', '3', 'A',
        '4', '5', '6', 'B',
        '7', '8', '9', 'C',
        '*', '0', '#', 'D'
    ]

    while not stop_event.is_set():
        if random.random() < 0.05:
            key = random.choice(keys)
            callback(key)
            time.sleep(0.3)

        time.sleep(interval)