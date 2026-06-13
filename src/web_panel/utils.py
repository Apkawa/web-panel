import os
import json

def load_config(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}
