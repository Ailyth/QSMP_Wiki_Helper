# QSMP 2 Wiki Helper

QSMP 2 Wiki Helper reads activity and VOD information from Google Sheets, combines the records by creator and date, and generates wiki-ready history templates.

The repository contains:

- A FastAPI backend in the repository root.
- A React/Vite browser frontend in `frontend/`.
- Shared parsing, merge, and wiki-generation logic.

## Deployment overview

The application runs as two services:

```text
Browser frontend -> FastAPI backend -> Google Sheets
```

For local development, run the backend and frontend on your computer. For Render, deploy them as two separate services:

- Backend: Render **Web Service**.
- Frontend: Render **Static Site**.

## Prerequisites

Install or create the following before deploying:

- Python 3.11 or newer.
- Node.js and npm for the frontend.
- A GitHub repository containing the source code.
- A Google service account with Viewer access to both spreadsheets.
- The spreadsheet URLs.

The backend reads these environment variables:

```text
ACTIVITY_SHEET_URL
VOD_SHEET_URL
GOOGLE_APPLICATION_CREDENTIALS
CORS_ORIGINS
```

## Important security rules

Never commit or upload these files to GitHub:

```text
service-account.json
credentials.json
token.json
```

They are ignored by `.gitignore`. If a private key has ever been exposed, revoke it in Google Cloud and create a replacement before deployment.

The Google service-account file belongs only to the backend hosting service. It must never be included in the frontend build.

## VOD output rules

VOD rows are grouped by canonical `Streamer` and normalized calendar date. The full `Stream Date` timestamp determines their order, so multiple streams on one day are emitted chronologically. URLs are read from `YouTube Vods URL` even when the URL belongs to Twitch, Kick, or another supported platform; the platform is detected from each URL.

The VOD is official when `Streamer` and `Channel` resolve to the same registered creator in `creators.json`. Otherwise it is unofficial. A single VOD is rendered as a platform-aware `Link` with `(official)` or `(unofficial)`. Multiple VODs are rendered as one numbered `OffStream` block. The reusable block shape is stored in `templates/off_stream.txt` and inserted into the day template.

## Local deployment

### 1. Get the code

From PowerShell:

```powershell
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Place your local `service-account.json` in the repository root for local testing. It must remain ignored by Git.

### 2. Start the backend locally

Create and activate a virtual environment from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Set the spreadsheet URLs. PowerShell example:

```powershell
$env:ACTIVITY_SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_ACTIVITY_ID"
$env:VOD_SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_VOD_ID"
$env:GOOGLE_APPLICATION_CREDENTIALS = "$PWD\service-account.json"
```

The service-account email must have Viewer access to both spreadsheets.

Start the API:

```powershell
uvicorn api:app --reload
```

Open the interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

Use `POST /api/refresh` first. Then test:

```text
GET /api/health
GET /api/overview
GET /api/creators
GET /api/vod-mismatches
```

Check syntax without accessing Google Sheets:

```powershell
python -m py_compile api.py service.py main.py
```

### 3. Start the frontend locally

Install Node.js, then run:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
```

Set `frontend/.env` to point to the backend:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```powershell
npm run dev
```

Open the Vite URL shown in the terminal, normally:

```text
http://localhost:5173
```

Keep the backend terminal running while using the frontend. The local frontend calls `http://127.0.0.1:8000` and the backend already allows the local Vite origins.

To build and preview the frontend as a production bundle:

```powershell
npm run build
npm run preview
```

## Render deployment

Deploy the backend first, then deploy the frontend. Do not put the service-account file in GitHub or in the frontend service.

### 1. Deploy the backend Web Service

The backend can be deployed as a Render Web Service directly from GitHub.

1. Push the repository to GitHub without sensitive files.
2. In Render, choose **New > Web Service**.
3. Connect the GitHub repository.
4. Use these settings:

```text
Root Directory: leave empty
Build Command: pip install -r requirements.txt
Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
```

5. Add these Render environment variables:

```text
ACTIVITY_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_ACTIVITY_ID
VOD_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_VOD_ID
```

6. Add the Google credentials under **Secret Files**, not as a normal GitHub file:

```text
Filename: service-account.json
```

7. Add this Render environment variable:

```text
GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/service-account.json
```

8. Deploy the service.

The backend URL will look like:

```text
https://YOUR-BACKEND.onrender.com
```

Test it by opening:

```text
https://YOUR-BACKEND.onrender.com/docs
```

Execute `POST /api/refresh` before using the data endpoints. A `GET` request to `/api/refresh` returns `405 Method Not Allowed` because refresh is intentionally a POST operation.

### 2. Deploy the frontend Static Site

Create a second Render service using **New > Static Site**.

Use these settings:

```text
Root Directory: frontend
Build Command: npm install && npm run build
Publish Directory: dist
```

Add this environment variable to the frontend Static Site:

```text
VITE_API_BASE_URL=https://YOUR-BACKEND.onrender.com
```

The value is embedded during the frontend build, so save it before deploying or manually trigger a new deploy after changing it.

The frontend URL will look like:

```text
https://YOUR-FRONTEND.onrender.com
```

### 3. Configure backend CORS

After the frontend is deployed, open the backend Web Service in Render and add:

```text
CORS_ORIGINS=https://YOUR-FRONTEND.onrender.com
```

Use the exact frontend origin without a trailing slash. Save the variable and redeploy the backend.

For local frontend development, the backend already allows:

```text
http://localhost:5173
http://127.0.0.1:5173
```

### 4. Use the deployed browser app

Open the frontend URL and select **Refresh data**. After a successful refresh:

- **Overview** shows creator, history, VOD, and review counts.
- **Creators** provides searchable creator history and wiki previews.
- **Timeline Tracking mismatches** lists unmatched VODs and supports CSV download.

## Troubleshooting

### `NetworkError` in the frontend

Check that:

- `VITE_API_BASE_URL` points to the backend URL, not `localhost`.
- `CORS_ORIGINS` contains the exact frontend URL.
- Both Render services have redeployed after their environment variables changed.

### `503 Service Unavailable` from a data endpoint

Call `POST /api/refresh` first. The API keeps refreshed data in memory and starts with no loaded data.

### `502 Bad Gateway` from refresh

Check the backend Render logs and verify:

- The secret file exists at `/etc/secrets/service-account.json`.
- `GOOGLE_APPLICATION_CREDENTIALS` has the correct path.
- The service account has Viewer access to both spreadsheets.
- Both spreadsheet URL environment variables are correct.

### `404` at the backend root URL

This is normal because the API does not define `/`. Use `/docs` or an `/api/...` endpoint instead.

## Current deployment limitation

The backend cache is stored in process memory. A service restart clears the refreshed data, so the application must be refreshed again. This is acceptable for an initial small deployment. A future production version should store refreshed data in a persistent database or managed datastore.
