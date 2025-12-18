import time
import random

def run_membrane_sim(delay, callback, stop_event, keys=4):
    while not stop_event.is_set():
        pressed = -1
        if random.random() < 0.05:
            pressed = random.randint(0, keys-1)
        callback(pressed)
        time.sleep(delay)