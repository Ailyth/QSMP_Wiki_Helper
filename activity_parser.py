from data_cleaning import normalize_name, canonical_name, parse_day
import json
import os

CREATOR_REGISTRY = {}

json_path = os.path.join(os.path.dirname(__file__), "creators.json")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert JSON keys into a set of canonical creator names
CREATOR_REGISTRY = set(data.keys())

def split_creators(cell_value):
    if not cell_value:
        return []

    # Replace common separators with commas
    separators = [",", "/", "&", ";","."]
    text = cell_value

    for sep in separators:
        text = text.replace(sep, ",")

    # Split and clean
    parts = [p.strip() for p in text.split(",")]

    # Remove empty entries
    return [p for p in parts if p]


def parse_activity_rows(rows, creator_registry):
    cleaned = []

    # Language columns (all except date/description/notes)
    creator_columns = [
        key for key in rows[0].keys()
        if key not in {"Day / date", "Description", "NOTES"}
    ]

    for row in rows:
        raw_day = row.get("Day / date", "").strip()
        if "/" not in raw_day:
            continue

        left, right = raw_day.split("/", 1)
        server_day = int(left.strip())

        day, month, year = right.strip().split(".")
        normalized_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Scan all language columns
        for col in creator_columns:
            raw_value = row.get(col, "").strip()

            if not raw_value:
                continue

            # Split multiple creators inside the cell
            creators = split_creators(raw_value)

            for c in creators:
                norm = normalize_name(c)
                canon = canonical_name(norm)

                cleaned.append({
                    "creator": canon,
                    "server_day": server_day,
                    "calendar_day": normalized_date
                })

                print("PARSED ACTIVITY:", normalized_date, server_day, canon)

    return cleaned

def parse_activity_sheets(sheets):
    all_rows = []
    date_to_server_day = {}

    allowed_months = {"June", "July"}  # TEMPORARY FILTER

    for ws in sheets:
        # Skip sheets outside allowed months
        if ws.title not in allowed_months:
            print("Skipping sheet:", ws.title)
            continue

        raw_values = ws.get_all_values()
        print("RAW HEADERS:", raw_values[0])

        # Skip sheets with empty headers
        if all(h.strip() == "" for h in raw_values[0]):
            print("Skipping empty-header sheet:", ws.title)
            continue

        # Fix empty headers
        headers = raw_values[0]
        fixed_headers = [
            h if h.strip() else f"EMPTY_{i}"
            for i, h in enumerate(headers)
        ]

        # Convert rows to dicts
        rows = [
            dict(zip(fixed_headers, row))
            for row in raw_values[1:]
        ]

        # Load alias registry
        with open("creators.json") as f:
            creator_registry = json.load(f)

        # Parse activity rows for this sheet
        parsed = parse_activity_rows(rows, creator_registry)

        # Build timeline mapping
        for row in parsed:
            server_day = row["server_day"]
            calendar_day = row["calendar_day"]
            date_to_server_day[calendar_day] = server_day

        all_rows.extend(parsed)

    return all_rows, date_to_server_day

