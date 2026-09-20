from datetime import datetime, timezone
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from service import RefreshResult, refresh_data
from wiki_generator import generate_creator_wiki, generate_day_block


app = FastAPI(title="QSMP 2 Wiki Helper API", version="1.0.0")

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_cached_result: RefreshResult | None = None
_last_refresh: datetime | None = None
_last_refresh_error: str | None = None


class HealthResponse(BaseModel):
    status: str
    data_loaded: bool
    last_refresh: datetime | None
    last_error: str | None


class RefreshResponse(BaseModel):
    status: str
    refreshed_at: datetime
    creator_count: int
    mismatch_count: int


class OverviewResponse(BaseModel):
    total_creators: int
    total_history_entries: int
    days_with_activity: int
    missing_vod_count: int
    mismatch_count: int
    last_refresh: datetime | None


class CreatorResponse(BaseModel):
    creator: str
    history: list[dict[str, Any]]


class WikiResponse(BaseModel):
    creator: str
    wiki: str


class MismatchResponse(BaseModel):
    mismatches: list[dict[str, Any]]
    count: int


def _require_data() -> RefreshResult:
    if _cached_result is None:
        raise HTTPException(
            status_code=503,
            detail="No data is loaded. Call POST /api/refresh first.",
        )
    return _cached_result


def _refresh_timestamp() -> datetime:
    return datetime.now(timezone.utc)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if _cached_result is not None else "not_ready",
        data_loaded=_cached_result is not None,
        last_refresh=_last_refresh,
        last_error=_last_refresh_error,
    )


@app.post("/api/refresh", response_model=RefreshResponse)
def refresh() -> RefreshResponse:
    global _cached_result, _last_refresh, _last_refresh_error

    try:
        result = refresh_data()
    except Exception as error:
        _last_refresh_error = str(error)
        raise HTTPException(
            status_code=502,
            detail="Unable to refresh data from the configured spreadsheets.",
        ) from error

    refreshed_at = _refresh_timestamp()
    _cached_result = result
    _last_refresh = refreshed_at
    _last_refresh_error = None

    return RefreshResponse(
        status="ok",
        refreshed_at=refreshed_at,
        creator_count=len(result.creators),
        mismatch_count=len(result.vod_mismatches),
    )


@app.get("/api/overview", response_model=OverviewResponse)
def overview() -> OverviewResponse:
    result = _require_data()
    history = [entry for entries in result.merged_data.values() for entry in entries]
    active_days = {
        entry["calendar_day"]
        for entry in history
        if isinstance(entry.get("server_day"), int)
    }
    missing_vods = [
        entry for entry in history
        if not entry.get("vods")
        or all(vod.get("url") == "UNAVAILABLE" for vod in entry["vods"])
    ]

    return OverviewResponse(
        total_creators=len(result.creators),
        total_history_entries=len(history),
        days_with_activity=len(active_days),
        missing_vod_count=len(missing_vods),
        mismatch_count=len(result.vod_mismatches),
        last_refresh=_last_refresh,
    )


@app.get("/api/creators", response_model=list[str])
def creators() -> list[str]:
    return _require_data().creators


@app.get("/api/creators/{creator}", response_model=CreatorResponse)
def creator_history(creator: str) -> CreatorResponse:
    result = _require_data()
    history = result.merged_data.get(creator)
    if history is None:
        raise HTTPException(status_code=404, detail=f"Creator not found: {creator}")

    return CreatorResponse(creator=creator, history=history)


@app.get("/api/creators/{creator}/wiki", response_model=WikiResponse)
def creator_wiki(
    creator: str,
    months: str | None = Query(default=None),
) -> WikiResponse:
    result = _require_data()
    history = result.merged_data.get(creator)
    if history is None:
        raise HTTPException(status_code=404, detail=f"Creator not found: {creator}")

    if months:
        selected_months = {
            month.strip().lower()
            for month in months.split(",")
            if month.strip()
        }
        history = [
            entry
            for entry in history
            if entry.get("wiki_date", "").split(maxsplit=1)[0].lower()
            in selected_months
        ]

        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"No history entries found for {creator} in the selected months",
            )

    return WikiResponse(
        creator=creator,
        wiki=generate_creator_wiki({creator: history}, creator),
    )


@app.get("/api/creators/{creator}/days/{calendar_day}/wiki", response_model=WikiResponse)
def creator_day_wiki(creator: str, calendar_day: str) -> WikiResponse:
    result = _require_data()
    history = result.merged_data.get(creator)
    if history is None:
        raise HTTPException(status_code=404, detail=f"Creator not found: {creator}")

    entry = next(
        (item for item in history if item.get("calendar_day") == calendar_day),
        None,
    )
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"No history entry found for {creator} on {calendar_day}",
        )

    return WikiResponse(
        creator=creator,
        wiki=generate_day_block(entry),
    )


@app.get("/api/vod-mismatches", response_model=MismatchResponse)
def vod_mismatches() -> MismatchResponse:
    mismatches = _require_data().vod_mismatches
    return MismatchResponse(mismatches=mismatches, count=len(mismatches))
