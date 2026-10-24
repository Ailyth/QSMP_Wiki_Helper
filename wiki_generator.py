import os

from logic import format_month_heading, format_wiki_date

VALID_LANGUAGES = {"en", "pl"}


def _validate_language(language):
    normalized = (language or "en").lower()
    if normalized not in VALID_LANGUAGES:
        raise ValueError(f"Unsupported language: {language!r}. Supported languages: {sorted(VALID_LANGUAGES)}")
    return normalized


def _load_template(template_name, language="en"):
    language = _validate_language(language)
    template_path = os.path.join("templates", f"{template_name}_{language}.txt")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as file:
        return file.read()


def format_status(record, language="en"):
    language = _validate_language(language)
    if record.get("official"):
        return "official" if language == "en" else "oficjalny"
    return "unofficial" if language == "en" else "nieoficjalny"


def build_vod_markup(entry, language="en"):
    language = _validate_language(language)
    records = entry.get("vods")
    if records is None:
        records = [{
            "url": entry.get("vod", "UNAVAILABLE"),
            "platform": "Youtube",
            "official": False,
            "timestamp": "",
        }]

    records = [
        record for record in records
        if record.get("url") not in (None, "", "UNAVAILABLE")
    ]
    if not records:
        return "UNAVAILABLE"

    creator = entry.get("creator", "")
    if len(records) == 1:
        record = records[0]
        platform = record.get("platform", "Youtube")
        return (
            f"{{{{Link|{platform}|url={record['url']}}}}} "
            f"({format_status(record, language)})"
        )

    template = _load_template("off_stream", language)
    partial_template = _load_template("off_stream_pov", language)

    fields = []
    for index, record in enumerate(records, start=1):
        suffix = "" if index == 1 else f" {index}"
        field_block = (
            partial_template
            .replace("{{INDEX}}", suffix)
            .replace("{{POV}}", creator)
            .replace("{{URL}}", record.get("url", ""))
            .replace("{{PLATFORM}}", record.get("platform", "Unknown"))
            .replace(
                "{{TIMESTAMP}}",
                f"{record.get('timestamp', '')} ({format_status(record, language)})"
            )
        )
        fields.append(field_block)

    return template.replace("{{OFF_STREAM_FIELDS}}", "\n".join(fields)).rstrip()


# -----------------------------
# Day Block Generator
# -----------------------------
def generate_day_block(entry, language="en"):
    language = _validate_language(language)
    template = _load_template("day", language)

    day = str(entry.get("server_day", ""))
    date = format_wiki_date(entry.get("calendar_day", entry.get("wiki_date", "1970-01-01")), language)
    vod_link = build_vod_markup(entry, language)

    return (
        template
        .replace("{{DAY}}", day)
        .replace("{{DATE}}", date)
        .replace("{{VOD_LINK}}", vod_link)
    )


# -----------------------------
# Month Block Generator
# -----------------------------
def generate_month_block(month_name, day_blocks, language="en"):
    language = _validate_language(language)
    template = _load_template("month", language)

    month_upper = month_name.upper()
    joined_days = "\n".join(day_blocks)

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
def generate_creator_wiki(merged_data, creator, language="en"):
    language = _validate_language(language)
    history = merged_data.get(creator, [])
    months = {}

    for entry in history:
        month_name = format_month_heading(entry.get("calendar_day", entry.get("wiki_date", "1970-01-01")), language)
        months.setdefault(month_name, []).append(entry)

    month_blocks = []

    for month_name, entries in months.items():
        day_blocks = [generate_day_block(e, language) for e in entries]
        month_block = generate_month_block(month_name, day_blocks, language)
        month_blocks.append(month_block)

    return "\n\n".join(month_blocks)
