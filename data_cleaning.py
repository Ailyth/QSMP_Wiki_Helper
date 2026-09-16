import json

# 1. Load creator database
with open("creators.json") as f:
    CREATORS = json.load(f)

# 2. Build alias map
ALIAS_MAP = {}

for canonical, data in CREATORS.items():
    for alias in data["aliases"]:
        ALIAS_MAP[alias.lower()] = canonical

# 3. Normalization functions
def normalize_name(name):
    return name.strip().lower()

def canonical_name(name):
    name = normalize_name(name)
    return ALIAS_MAP.get(name, name)

# 4. Day parsing
def parse_day(raw_day):
    # raw_day example: "110/ 01.07.2026"
    parts = raw_day.split("/")
    server_day = parts[0].strip()

    raw_date = parts[1].strip()  # "01.07.2026"
    d, m, y = raw_date.split(".")

    calendar_day = f"{y}-{m}-{d}"  # "2026-07-01"

    return server_day, calendar_day
