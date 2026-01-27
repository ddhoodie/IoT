import threading
import time
from devices.base import SensorBase
from simulators.webcam_sim import run_webcam_sim
from core.console import safe_print, print_prompt
from core.mqtt_publisher import mqtt_publisher
import settings

class WebcamSensor(SensorBase):
    """a little bit of tomfoolery"""

    def start(self, threads, stop_event):
        interval = self.cfg.get("interval", 5.0)
        is_simulated = self.cfg.get("simulated", True)

        def callback(frame_id, event_type, metadata):
            ts = time.strftime("%H:%M:%S")

            if event_type == "no_activity":
                return

            meta_str = ", ".join([f"{k}={v}" for k, v in metadata.items()])

            emoji_map = {
                "person_detected": "🚶",
                "motion_detected": "📹",
                "face_detected": "👤",
                "package_detected": "📦"
            }
            emoji = emoji_map.get(event_type, "📷")

            safe_print(f"\n[{ts}] {self.code} {emoji} frame#{frame_id} {event_type} ({meta_str})")
            print_prompt()

            data = {
                "measurement": "Webcam",
                "pi": settings.settings.get("PI", "unknown"),
                "device": self.cfg.get("name", self.code),
                "code": self.code,
                "value": {
                    "event": event_type,
                    "frame_id": frame_id,
                    **metadata
                },
                "simulated": is_simulated,
                "timestamp": time.time()
            }
            mqtt_publisher.publish_data("Webcam", data)

        if self.cfg.get("simulated", True):
            t = threading.Thread(
                target=run_webcam_sim,
                args=(interval, callback, stop_event),
                daemon=True
            )
            t.start()
            threads.append(t)
            return

        # TODO: Pravi webcam
        safe_print(f"Real webcam not implemented yet for {self.code}, using simulation")
        t = threading.Thread(
            target=run_webcam_sim,
            args=(interval, callback, stop_event),
            daemon=True
        )
        t.start()
        threads.append(t)