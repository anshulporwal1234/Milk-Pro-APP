# ==============================
# Milk Diary Pro
# config.py
# ==============================

import os
import json

DATABASE_NAME = "milk.db"
CONFIG_FILE = "config.json"

DEFAULT_SETTINGS = {
    "milk_rate": 65.0,
    "owner_name": "Owner Name",
    "customer_name": "Customer Name",
    "email": "",
    "phone": "",
    "notifications": True,
    "backup_folder": "backups"
}

def load_settings():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)
        return DEFAULT_SETTINGS
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return DEFAULT_SETTINGS

def save_settings(settings_data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(settings_data, f, indent=4)

REPORT_FOLDER = "reports"
if not os.path.exists(REPORT_FOLDER):
    os.makedirs(REPORT_FOLDER)

MILK_OPTIONS = ["0", "0.5", "1", "Other"]
APP_NAME = "Milk Diary Pro"
THEME = "flatly"
