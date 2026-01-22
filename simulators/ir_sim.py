import time
import random


def run_ir_sim(interval, callback, stop_event):
    detected = False

    while not stop_event.is_set():
        if random.random() < 0.2:
            if not detected:
                detected = True
                callback(detected)
                hold_time = random.uniform(1.0, 3.0)
                time.sleep(hold_time)
        else:
            if detected:
                detected = False
                callback(detected)

        time.sleep(interval)