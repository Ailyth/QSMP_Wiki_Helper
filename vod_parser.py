from data_cleaning import canonical_name, normalize_calendar_date, is_excluded_creator

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
    title_col = None

    for key in row.keys():
        normalized = key.lower().replace(" ", "").replace("/", "").replace("-", "").replace("\n", "")

        # Must match "streamdate", not "day"
        if "streamdate" in normalized:
            date_col = key

        elif "streamer" in normalized:
            creator_col = key

        elif "youtubevodsurl" in normalized:
            vod_col = key
        elif "youtubevodstitle" in normalized:
            title_col = key

    return date_col, creator_col, vod_col, title_col

def parse_vod_rows(rows):
    index = {}

    date_col, creator_col, vod_col, title_col = detect_columns(rows[0])

    if not date_col or not creator_col or not vod_col:
        raise ValueError("Could not detect required VOD columns.")

    for row in rows:
        raw_creator = row[creator_col]

        raw_date = row[date_col]

        date = normalize_calendar_date(raw_date)
        if date is None:
            if str(raw_date).strip().upper() not in {"", "N/A", "NA", "-"}:
                print("Skipping invalid VOD date:", raw_date)
            continue

        # Normalize + canonicalize creator
        if is_excluded_creator(raw_creator):
            continue

        creator = canonical_name(raw_creator)

        vod = row[vod_col]
        title = row.get(title_col, "") if title_col else ""

        # print("VOD KEY:", creator, date, "→", vod)
        index[(creator, date)] = {"url": vod, "title": title}

    return index

def parse_vod_sheets(sheets):
    vod_index = {}

    for ws in sheets:
        parts = ws.title.split()
        if len(parts) != 2:
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
