import time
import random

def run_ultrasonic_sim(delay, callback, stop_event):
    dist = 120.0
    while not stop_event.is_set():
        dist += random.uniform(-5, 5)
        dist = max(2.0, min(300.0, dist))
        callback(dist)
        time.sleep(delay)