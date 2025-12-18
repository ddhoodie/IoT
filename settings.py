import json

def load_settings(file_path="settings.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)