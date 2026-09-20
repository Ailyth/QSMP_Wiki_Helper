import os


def format_status(record):
    return "official" if record.get("official") else "unofficial"


def build_vod_markup(entry):
    records = entry.get("vods")
    if records is None:
        records = [{
            "url": entry.get("vod", "UNAVAILABLE"),
            "platform": "Youtube",
            "official": False,
            "timestamp": "",
        }]

    records = [record for record in records if record.get("url") != "UNAVAILABLE"]
    if not records:
        return "UNAVAILABLE"

    creator = entry.get("creator", "")
    if len(records) == 1:
        record = records[0]
        platform = record.get("platform", "Youtube")
        return (
            f"{{{{Link|{platform}|url={record['url']}}}}} "
            f"({format_status(record)})"
        )

    template_path = os.path.join("templates", "off_stream.txt")
    with open(template_path, "r", encoding="utf-8") as file:
        template = file.read()

    fields = []
    for index, record in enumerate(records, start=1):
        suffix = "" if index == 1 else f" {index}"
        fields.extend([
            f"|pov{suffix}={creator}",
            f"|url{suffix}={record['url']}",
            f"|platform{suffix}={record.get('platform', 'Unknown')}",
            f"|timestamp{suffix}={record.get('timestamp', '')} ({format_status(record)})",
        ])

    return template.replace("{{OFF_STREAM_FIELDS}}", "\n".join(fields)).rstrip()

# -----------------------------
# Day Block Generator
# -----------------------------
def generate_day_block(entry):
    template_path = os.path.join("templates", "day.txt")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    day = str(entry["server_day"])
    date = entry["wiki_date"]      # already wiki formatted
    vod_link = build_vod_markup(entry)

    return (
        template
        .replace("{{DAY}}", day)
        .replace("{{DATE}}", date)
        .replace("{{VOD_LINK}}", vod_link)
    )


# -----------------------------
# Month Block Generator
# -----------------------------
def generate_month_block(month_name, day_blocks):
    # 1. Load month template
    template_path = os.path.join("templates", "month.txt")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 2. Prepare replacements
    month_upper = month_name.upper()
    joined_days = "\n".join(day_blocks)

    # 3. Replace placeholders
    block = (
        template
        .replace("{{MONTH_NAME}}", month_name)
        .replace("{{MONTH_NAME_UPPER}}", month_upper)
        .replace("{{DAY_BLOCKS}}", joined_days)
    )

    return block


# -----------------------------
# Creator Wiki Generator
# -----------------------------
def generate_creator_wiki(merged_data, creator):
    # 1. Get full history for this creator
    history = merged_data.get(creator, [])

    # 2. Group entries by month name
    months = {}

    for entry in history:
        # calendar_day is already formatted: "April 25th, 2026"
        formatted_date = entry["wiki_date"]
        month_name = formatted_date.split()[0]


        # Extract month name (first word)
        month_name = formatted_date.split()[0]

        if month_name not in months:
            months[month_name] = []

        months[month_name].append(entry)

    # 3. Build month blocks
    month_blocks = []

    for month_name, entries in months.items():
        # Generate day blocks for this month
        day_blocks = [generate_day_block(e) for e in entries]

        # Generate month block
        month_block = generate_month_block(month_name, day_blocks)
        month_blocks.append(month_block)

    # 4. Join all month blocks
    return "\n\n".join(month_blocks)
