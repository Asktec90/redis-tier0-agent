#!/usr/bin/env python3

import yaml
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "state" / "snapshots.json"

STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_config():
    with open(BASE_DIR / "config.yaml") as f:
        return yaml.safe_load(f)

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def write_report(path, text):
    path.write_text(text)

