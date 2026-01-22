import json
import sys


def load_settings(file_path=None):
    if file_path is None:
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
        else:
            file_path = "settings_P1.json"  # Default

    print(f"Loading config: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)