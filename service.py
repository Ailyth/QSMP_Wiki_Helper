import json
import os
from dataclasses import dataclass
from typing import Any

from activity_parser import parse_activity_sheets
from data_loader import authorize, get_all_sheets, get_month_sheets, load_sheet
from logic import (
    find_vod_without_activity,
    get_all_creators,
    group_days_by_creator,
    merge_activity_with_vods,
)
from vod_parser import parse_vod_sheets


ACTIVITY_URL = "https://docs.google.com/spreadsheets/d/1sOnTqp0W_VwtJTcp3o67gbX5q4HqnkcLuj8dXNtAoic"
VOD_URL = "https://docs.google.com/spreadsheets/d/1yKkzNTjkFzyqNsUPRkWoqHtqDeOD9FoCjjDmzIJn_gE"
CREATORS_PATH = os.path.join(os.path.dirname(__file__), "creators.json")


@dataclass
class RefreshResult:
    creators: list[str]
    merged_data: dict[str, list[dict[str, Any]]]
    vod_mismatches: list[dict[str, Any]]


def refresh_data() -> RefreshResult:
    gspread_client = authorize()

    activity_sheet = load_sheet(gspread_client, ACTIVITY_URL)
    vod_sheet = load_sheet(gspread_client, VOD_URL)

    activity_sheets = get_all_sheets(activity_sheet)
    vod_sheets = get_month_sheets(vod_sheet)

    activity_rows, timeline_date_to_day = parse_activity_sheets(activity_sheets)
    vod_index = parse_vod_sheets(vod_sheets)
    grouped = group_days_by_creator(activity_rows)

    with open(CREATORS_PATH, encoding="utf-8") as file:
        creators_json = json.load(file)

    merged_data = merge_activity_with_vods(
        grouped,
        vod_index,
        creators_json,
        timeline_date_to_day,
    )

    return RefreshResult(
        creators=get_all_creators(merged_data),
        merged_data=merged_data,
        vod_mismatches=find_vod_without_activity(grouped, vod_index),
    )
