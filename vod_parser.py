from data_cleaning import normalize_name, canonical_name

def is_month_sheet(name):
    parts = name.split()
    if len(parts) != 2:
        return False

    month, year = parts
    return month.isalpha() and year.isdigit()

def detect_columns(row):
    date_col = None
    creator_col = None
    vod_col = None

    for key in row.keys():
        normalized = key.lower().replace(" ", "").replace("/", "").replace("-", "").replace("\n", "")

        # Must match "streamdate", not "day"
        if "streamdate" in normalized:
            date_col = key

        elif "streamer" in normalized:
            creator_col = key

        elif "youtubevodsurl" in normalized:
            vod_col = key

    return date_col, creator_col, vod_col

def parse_vod_rows(rows):
    index = {}

    date_col, creator_col, vod_col = detect_columns(rows[0])

    if not date_col or not creator_col or not vod_col:
        raise ValueError("Could not detect required VOD columns.")

    for row in rows:
        raw_creator = row[creator_col]

        raw_date = row[date_col]

        # Normalize date
        date = raw_date.split("T")[0].replace("/", "-")

        # Normalize + canonicalize creator
        creator = canonical_name(raw_creator)

        vod = row[vod_col]

        # print("VOD KEY:", creator, date, "→", vod)
        index[(creator, date)] = vod

    return index

def parse_vod_sheets(sheets):
    vod_index = {}

    allowed_months = {"June", "July"}

    for ws in sheets:
        # Skip sheets not in allowed months
        parts = ws.title.split()
        if len(parts) != 2:
            continue

        month, year = parts
        if month not in allowed_months:
            continue

        raw_values = ws.get_all_values()

        headers = raw_values[0]
        fixed_headers = [
            h if h.strip() else f"EMPTY_{i}"
            for i, h in enumerate(headers)
        ]

        rows = [
            dict(zip(fixed_headers, row))
            for row in raw_values[1:]
        ]

        parsed = parse_vod_rows(rows)
        vod_index.update(parsed)

    return vod_index
