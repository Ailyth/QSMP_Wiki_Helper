import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from vod_parser import is_month_sheet
import os


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def authorize():
    # Open OAuth in Firefox private window
    os.environ["BROWSER"] = "firefox --private-window"

    creds = None

    # Load token.json if it exists
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If no valid token, do OAuth login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token.json
        with open("token.json", "w") as token:
            token.write(creds.to_json())

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
