import time
import random

def run_pir_sim(delay, callback, stop_event):
    while not stop_event.is_set():
        motion = 1 if random.random() < 0.05 else 0
        callback(motion)
        time.sleep(delay)