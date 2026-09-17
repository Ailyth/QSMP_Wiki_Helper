import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

credentials = Credentials.from_service_account_file(
    "service-account.json",
    scopes=SCOPES,
)

client = gspread.authorize(credentials)

# ACTIVITY_URL = "https://docs.google.com/spreadsheets/d/1sOnTqp0W_VwtJTcp3o67gbX5q4HqnkcLuj8dXNtAoic"
# VOD_URL = "https://docs.google.com/spreadsheets/d/1yKkzNTjkFzyqNsUPRkWoqHtqDeOD9FoCjjDmzIJn_gE"
for url in [
    "https://docs.google.com/spreadsheets/d/1sOnTqp0W_VwtJTcp3o67gbX5q4HqnkcLuj8dXNtAoic",
    "https://docs.google.com/spreadsheets/d/1yKkzNTjkFzyqNsUPRkWoqHtqDeOD9FoCjjDmzIJn_gE",
]:
    spreadsheet = client.open_by_url(url)
    print("Success:", spreadsheet.title)