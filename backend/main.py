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

import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from gemini_service import match_tenders_with_gemini  # noqa: E402
from models import CompanyProfile, MatchTendersResponse  # noqa: E402
from tender_loader import TenderCache  # noqa: E402

TENDERS_DIR = os.environ.get("TENDERS_DIR", "./tenders")
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
