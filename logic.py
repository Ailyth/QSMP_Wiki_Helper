# -----------------------------
# Date Formatting
# -----------------------------
def convert_date_to_wiki_format(date_str):
    """
    Converts dates from formats like:
    - 'DD.MM.YYYY'
    - 'YYYY-MM-DD'
    - 'DD/MM/YYYY'
    into the wiki format: 'YYYY-MM-DD'
    """

    if "-" in date_str and len(date_str.split("-")[0]) == 4:
        return date_str

    if "." in date_str:
        day, month, year = date_str.split(".")
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    if "/" in date_str:
        day, month, year = date_str.split("/")
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    return date_str


def format_wiki_date(date_str):
    # Input: "2026-06-02"
    # Output: "June 2nd, 2026"

    year, month, day = date_str.split("-")
    day = int(day)

    months = {
        "01": "January", "02": "February", "03": "March",
        "04": "April",   "05": "May",      "06": "June",
        "07": "July",    "08": "August",   "09": "September",
        "10": "October", "11": "November", "12": "December"
    }

    if 11 <= day <= 13:
        suffix = "th"
    else:
        last = day % 10
        if last == 1:
            suffix = "st"
        elif last == 2:
            suffix = "nd"
        elif last == 3:
            suffix = "rd"
        else:
            suffix = "th"

    month_name = months[month]
    return f"{month_name} {day}{suffix}, {year}"


# -----------------------------
# Merge Logic
# -----------------------------
def merge_activity_with_vods(grouped_activity, vod_index, creators_json, timeline_date_to_day):
    merged = {}

    allowed_creators = set(creators_json.keys())
    all_days = set()

    # Collect activity days
    for creator, days in grouped_activity.items():
        if creator in allowed_creators:
            for entry in days:
                all_days.add((creator, entry["calendar_day"]))

    # Collect VOD days
    for (creator, date) in vod_index.keys():
        if creator in allowed_creators:
            all_days.add((creator, date))

    # Merge
    for creator, date in sorted(all_days):

        # DEBUG 1 — show what merge is trying to match
        # print("MERGE CHECK:", creator, date)

        # Find activity entry
        activity_entry = next(
            (e for e in grouped_activity.get(creator, []) if e["calendar_day"] == date),
            None
        )

        if activity_entry:
            server_day = activity_entry["server_day"]
        else:
            server_day = timeline_date_to_day.get(date, "—")

        # DEBUG 2 — show server day decision
        # print("SERVER DAY DECISION:", creator, date, "→", server_day)

        # Find VOD
        vod = vod_index.get((creator, date), "UNAVAILABLE")

        # DEBUG 3 — show VOD match
        # print("VOD MATCH:", creator, date, "→", vod)

        merged.setdefault(creator, []).append({
            "server_day": server_day,
            "calendar_day": date,
            "wiki_date": format_wiki_date(date),
            "vod": vod
        })

    return merged

# -----------------------------
# Grouping + Helpers
# -----------------------------
def group_days_by_creator(activity_rows):
    grouped = {}

    for row in activity_rows:
        creator = row["creator"]

        if creator not in grouped:
            grouped[creator] = []

        grouped[creator].append({
            "server_day": row["server_day"],
            "calendar_day": row["calendar_day"]
        })

    return grouped


def get_all_creators(merged_data):
    return sorted(merged_data.keys())


def get_creator_full_history(merged_data, creator):
    return merged_data.get(creator, [])
