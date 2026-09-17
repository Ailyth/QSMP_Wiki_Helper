# Abandoned CCS frontend

## Local development

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

The default API URL is `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` in `.env` to use the deployed API.

## Production build

```powershell
npm run build
npm run preview
```

The frontend expects the FastAPI backend to expose the endpoints in the repository root `api.py`.
