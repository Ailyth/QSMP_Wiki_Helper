import gspread
from google.oauth2.service_account import Credentials
from vod_parser import is_month_sheet
import os


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(__file__),
    "service-account.json"
)

def authorize():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH,
        scopes=SCOPES
    )
    return gspread.authorize(creds)

def load_sheet(gc, url):
    return gc.open_by_url(url)


def get_all_sheets(sheet):
    return sheet.worksheets()


def get_month_sheets(sheet):
    month_sheets = []
    for ws in sheet.worksheets():
        if is_month_sheet(ws.title):
            month_sheets.append(ws)
    return month_sheets


def get_rows(ws):
    return ws.get_all_records()
