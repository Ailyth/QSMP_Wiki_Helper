import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from data_cleaning import CREATORS, canonical_name, normalize_calendar_date, is_excluded_creator


PLATFORM_HOSTS = {
    "youtube.com": "Youtube",
    "youtu.be": "Youtube",
    "twitch.tv": "Twitch",
    "twitter.com": "Twitter",
    "x.com": "Twitter",
    "kick.com": "Kick",
    "afreecatv.com": "AfreecaTV",
    "chzzk.naver.com": "CHZZK",
    "cinefy.com": "Cinefy",
    "naver.com": "Naver",
    "apps.apple.com": "AppStore",
    "instagram.com": "Instagram",
    "play.google.com": "GooglePlay",
    "tiktok.com": "Tiktok",
    "nicovideo.jp": "Niconico",
}

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
    channel_col = None

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
        elif normalized == "channel":
            channel_col = key

    return date_col, creator_col, vod_col, title_col, channel_col


def parse_stream_timestamp(value, source_order):
    raw_value = str(value).strip()
    normalized = raw_value.replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return (datetime.max.replace(tzinfo=timezone.utc), source_order), raw_value

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return (parsed.astimezone(timezone.utc), source_order), parsed.strftime("%H:%M:%S")


def detect_platform(url):
    hostname = urlparse(url).hostname or ""
    hostname = hostname.lower().removeprefix("www.")

    for host, platform in PLATFORM_HOSTS.items():
        if hostname == host or hostname.endswith(f".{host}"):
            return platform

    return "Unknown"

def parse_vod_rows(rows):
    index = {}

    if not rows:
        return index

    date_col, creator_col, vod_col, title_col, channel_col = detect_columns(rows[0])

    if not date_col or not creator_col or not vod_col:
        raise ValueError("Could not detect required VOD columns.")

    for source_order, row in enumerate(rows):
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
        channel = canonical_name(row.get(channel_col, "")) if channel_col else ""
        official = creator in CREATORS and creator == channel

        vod_urls = [url.strip() for url in re.split(r"(?=https?://)", str(row[vod_col])) if url.strip()]
        vod_urls = [url for url in vod_urls if url.upper() not in {"N/A", "NA", "-"}]
        title = row.get(title_col, "") if title_col else ""
        sort_key, display_timestamp = parse_stream_timestamp(raw_date, source_order)

        records = [
            {
                "url": url,
                "title": title,
                "platform": detect_platform(url),
                "official": official,
                "timestamp": display_timestamp,
                "sort_key": sort_key,
            }
            for url in vod_urls
        ]
        if not records:
            records = [{
                "url": "UNAVAILABLE",
                "title": title,
                "platform": "Unknown",
                "official": official,
                "timestamp": display_timestamp,
                "sort_key": sort_key,
            }]

        index.setdefault((creator, date), []).extend(records)

    for records in index.values():
        records.sort(key=lambda record: record["sort_key"])
        for record in records:
            record.pop("sort_key", None)

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
        for key, records in parsed.items():
            vod_index.setdefault(key, []).extend(records)

    for records in vod_index.values():
        records.sort(key=lambda record: record.get("timestamp", ""))

    return vod_index
