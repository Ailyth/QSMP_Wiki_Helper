import json
import os
from datetime import datetime

# 1. Load creator database
with open(os.path.join(os.path.dirname(__file__), "creators.json"), encoding="utf-8") as f:
    CREATORS = json.load(f)

with open(os.path.join(os.path.dirname(__file__), "excluded_creators.json"), encoding="utf-8") as f:
    EXCLUDED_CREATORS = {name.strip().lower() for name in json.load(f)}

# 2. Build alias map
ALIAS_MAP = {}

for canonical, data in CREATORS.items():
    ALIAS_MAP[canonical.lower()] = canonical
    display_name = data.get("display", canonical)
    ALIAS_MAP[display_name.lower()] = canonical
    for alias in data["aliases"]:
        ALIAS_MAP[alias.lower()] = canonical

# 3. Normalization functions
def normalize_name(name):
    return name.strip().lower()

def canonical_name(name):
    name = normalize_name(name)
    return ALIAS_MAP.get(name, name)


def is_excluded_creator(name):
    return normalize_name(name) in EXCLUDED_CREATORS


def normalize_calendar_date(value):
    value = str(value).strip().split("T", 1)[0]

    for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            parsed = datetime.strptime(value, date_format)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None

# 4. Day parsing
def parse_day(raw_day):
    # raw_day example: "110/ 01.07.2026"
    parts = raw_day.split("/")
    server_day = parts[0].strip()

    raw_date = parts[1].strip()  # "01.07.2026"
    d, m, y = raw_date.split(".")

    calendar_day = f"{y}-{m}-{d}"  # "2026-07-01"

    return server_day, calendar_day
