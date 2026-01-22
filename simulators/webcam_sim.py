import time
import random


def run_webcam_sim(interval, callback, stop_event):
    frame_id = 0

    events = [
        "person_detected",
        "motion_detected",
        "face_detected",
        "package_detected",
        "no_activity"
    ]

    person_names = ["Unknown Person", "Delivery Person", "Resident", "Guest"]

    while not stop_event.is_set():
        frame_id += 1

        if random.random() < 0.7:
            event_type = "no_activity"
            metadata = {}
        else:
            event_type = random.choice(events[:-1])  # Bez "no_activity"

            metadata = {}

            if event_type == "person_detected":
                metadata = {
                    "count": random.randint(1, 3),
                    "confidence": round(random.uniform(0.7, 0.99), 2)
                }

            elif event_type == "motion_detected":
                metadata = {
                    "intensity": random.choice(["low", "medium", "high"]),
                    "location": random.choice(["left", "center", "right"])
                }

            elif event_type == "face_detected":
                metadata = {
                    "identity": random.choice(person_names),
                    "confidence": round(random.uniform(0.6, 0.95), 2)
                }

            elif event_type == "package_detected":
                metadata = {
                    "size": random.choice(["small", "medium", "large"]),
                    "position": random.choice(["doorstep", "porch", "ground"])
                }

        callback(frame_id, event_type, metadata)
        time.sleep(interval)