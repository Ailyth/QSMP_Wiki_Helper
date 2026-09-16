from data_loader import authorize, load_sheet, get_all_sheets, get_month_sheets
from activity_parser import parse_activity_sheets
from vod_parser import parse_vod_sheets
from logic import (
    group_days_by_creator,
    merge_activity_with_vods,
    get_all_creators
)
import json

from gui.gui import run_app

ACTIVITY_URL = "https://docs.google.com/spreadsheets/d/1sOnTqp0W_VwtJTcp3o67gbX5q4HqnkcLuj8dXNtAoic"
VOD_URL = "https://docs.google.com/spreadsheets/d/1yKkzNTjkFzyqNsUPRkWoqHtqDeOD9FoCjjDmzIJn_gE"

def main():
    # 1. Authenticate
    gc = authorize()

    # 2. Load spreadsheets
    activity_sheet = load_sheet(gc, ACTIVITY_URL)
    vod_sheet = load_sheet(gc, VOD_URL)

    # 3. Load sheets inside spreadsheets
    activity_sheets = get_all_sheets(activity_sheet)
    vod_sheets = get_month_sheets(vod_sheet)

    # 4. Parse activity (unified: activity + timeline)
    activity_rows, timeline_date_to_day = parse_activity_sheets(activity_sheets)

    # 5. Parse VODs
    vod_index = parse_vod_sheets(vod_sheets)

    # 6. Group activity by creator
    grouped = group_days_by_creator(activity_rows)
    # print("GROUPED ACTIVITY FOR MAXIMUS:", grouped.get("Maximus"))

    # 7. Load JSON creators
    with open("creators.json") as f:
        creators_json = json.load(f)

    # 8. Merge activity + VODs
    merged = merge_activity_with_vods(
        grouped,
        vod_index,
        creators_json,
        timeline_date_to_day
    )

    # 9. Extract creator list
    creators = get_all_creators(merged)

    # 10. Run GUI
    run_app(creators, merged)

if __name__ == "__main__":
    main()