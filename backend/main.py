"""
FastAPI backend for tender matching.

Run with:
    uvicorn main:app --reload --port 8000

Then in your Next.js frontend .env.local:
    NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

The frontend's api.ts posts to `${API_BASE_URL}/tenders/match` — that's
exactly the route defined below.
"""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from gemini_service import match_tenders_with_gemini  # noqa: E402
from models import CompanyProfile, MatchTendersResponse  # noqa: E402
from tender_loader import TenderCache  # noqa: E402

# Always resolve relative to this file's own location, not the current
# working directory — so paths land in the same place regardless of how or
# from where the process was started (double-click, Task Scheduler, IDE,
# a different machine, etc.). Still overridable via env var with an
# absolute path if you ever want the data to live elsewhere.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)  # one level above the backend/ folder
TENDERS_DIR = os.environ.get("TENDERS_DIR", os.path.join(BASE_DIR, "tenders"))
COMPANY_PROFILE_FILE = os.path.join(PARENT_DIR, "company_details.json")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app = FastAPI(title="Tender Matching API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

cache = TenderCache(TENDERS_DIR)


@app.get("/health")
def health():
    docs = cache.get_all()
    return {
        "status": "ok",
        "tendersDir": os.path.abspath(TENDERS_DIR),
        "tendersLoaded": len(docs),
        "loadErrors": cache.get_errors(),
    }


@app.post("/admin/reload")
def reload_tenders():
    """Force an immediate reload of all .md files, bypassing the mtime cache."""
    return cache.reload()


@app.post("/tenders/match", response_model=MatchTendersResponse)
def match_tenders(profile: CompanyProfile):
    # Save the incoming profile to disk as JSON every time "Find Tender"
    # is clicked (overwrites the previous file with the latest submission).
    try:
        with open(COMPANY_PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile.model_dump(), f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Warning: could not write company_details.json: {e}")

    docs = cache.get_all()  # auto-refreshes anything changed on disk

    if not docs:
        errors = cache.get_errors()
        detail = "No tender .md files could be loaded."
        if errors:
            detail += f" Errors: {errors}"
        raise HTTPException(status_code=503, detail=detail)

    try:
        matches = match_tenders_with_gemini(profile, docs)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return MatchTendersResponse(matches=matches)