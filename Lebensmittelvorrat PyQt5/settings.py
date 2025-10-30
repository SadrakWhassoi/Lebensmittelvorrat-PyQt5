import json
import os

SETTINGS_FILE = "settings.json"

def load_theme():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            try:
                return json.load(f).get("theme", "light")
            except:
                return "light"
    return "light"

def save_theme(theme):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"theme": theme}, f)