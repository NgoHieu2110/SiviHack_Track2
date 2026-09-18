"""
FastAPI backend for tender matching.

Run with:
    uvicorn main:app --reload --port 8000

Then in your Next.js frontend .env.local:
    NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

The frontend's api.ts posts to `${API_BASE_URL}/tenders/match` -- that's
exactly the route defined below.

WHAT /tenders/match DOES NOW
-----------------------------
POST /tenders/match no longer does a one-shot AI scoring pass against a
pre-loaded corpus of tender markdown. Instead it runs the *entire* workflow
pipeline live, for the single company profile just submitted, and streams
progress back to the browser as Server-Sent Events (`text/event-stream`)
over the same POST response body:

    1. Save the submitted profile into company_details.json, under an
       auto-generated, ephemeral company name (the live form has no "company
       name" field, and workflow_tools/*.py key everything off one) --
       see 1_company_md_to_company_details.py's schema for context.
    2. workflow_tools/2_company_details_to_initial_filter.py: ask Gemini to
       turn that profile into a filters.yaml block (CPV/NUTS prefixes,
       value range, exclusions, role hints).
    3. workflow_tools/3_run_filter_for_tenders.py: walk oeffentlichevergabe.de
       backward day by day until PIPELINE_TARGET_COUNT tenders match, or
       PIPELINE_MAX_DAYS_BACK is hit.
    4. workflow_tools/4_standardize_tenders.py: normalize the raw hits into
       the standardized schema.
    5. workflow_tools/5_select_tendars.py: pick PIPELINE_SELECT_COUNT of
       them at random.

Each SSE event is one line of JSON after "data: ":
    {"type": "progress", "stage": "...", "message": "..."}   (many)
    {"type": "done", "matches": [...]}                         (one, on success)
    {"type": "error", "message": "..."}                        (one, on failure)

This is a genuinely slow, external-API-bound operation (a Gemini call plus
however many days of oeffentlichevergabe.de fetches it takes), which is why
it streams progress rather than returning a single blocking JSON response.

Also exposes POST /admin/save-company-profile, which writes whatever
CompanyProfile is POSTed to it into company_details.json directly, without
running the rest of the pipeline -- useful for pre-registering real
companies that a scheduled/batch run of workflow_tools 2-4 will pick up
later, as opposed to the ephemeral live-search companies /tenders/match
creates.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import queue
import re
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402

from models import CompanyProfile, Tender, TenderMatch  # noqa: E402

# ---------------------------------------------------------------------------
# Paths. Defaults assume the layout documented in 3_run_filter_for_tenders.py:
#
#   backend/
#     main.py                      <- this file
#     oeffentlichevergabe/
#       fetch_tenders_oeffentlichevergabe.py
#     workflow_tools/
#       1_company_md_to_company_details.py
#       2_company_details_to_initial_filter.py
#       3_run_filter_for_tenders.py
#       4_standardize_tenders.py
#       5_select_tendars.py
#       company_details.json
#     tenders/                     <- raw fetch output
#     standardized_tenders/        <- standardized output
#
# Every path is overridable via env var if your layout differs.
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
WORKFLOW_TOOLS_DIR = Path(os.environ.get("WORKFLOW_TOOLS_DIR", BASE_DIR / "workflow_tools"))
FETCH_MODULE_PATH = Path(
    os.environ.get("FETCH_MODULE_PATH", BASE_DIR / "oeffentlichevergabe" / "fetch_tenders_oeffentlichevergabe.py")
)
COMPANY_DETAILS_PATH = Path(os.environ.get("COMPANY_DETAILS_PATH", WORKFLOW_TOOLS_DIR / "company_details.json"))
TENDERS_DIR = Path(os.environ.get("TENDERS_DIR", BASE_DIR / "tenders"))
STANDARDIZED_TENDERS_DIR = Path(os.environ.get("STANDARDIZED_TENDERS_DIR", BASE_DIR / "standardized_tenders"))

FILTER_SCRIPT_PATH = Path(os.environ.get("FILTER_SCRIPT_PATH", WORKFLOW_TOOLS_DIR / "2_company_details_to_initial_filter.py"))
FETCH_FILTER_RUNNER_PATH = Path(os.environ.get("FETCH_FILTER_RUNNER_PATH", WORKFLOW_TOOLS_DIR / "3_run_filter_for_tenders.py"))
STANDARDIZE_SCRIPT_PATH = Path(os.environ.get("STANDARDIZE_SCRIPT_PATH", WORKFLOW_TOOLS_DIR / "4_standardize_tenders.py"))
SELECT_SCRIPT_PATH = Path(os.environ.get("SELECT_SCRIPT_PATH", WORKFLOW_TOOLS_DIR / "5_select_tendars.py"))

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# How many tenders the fetch stage tries to collect before we randomly pick
# PIPELINE_SELECT_COUNT of them, how many days back it's allowed to walk to
# get there, and how many we finally show. Kept small by default since this
# now runs live, in the request path, for a single ephemeral company.
PIPELINE_TARGET_COUNT = int(os.environ.get("PIPELINE_TARGET_COUNT", "6"))
PIPELINE_MAX_DAYS_BACK = int(os.environ.get("PIPELINE_MAX_DAYS_BACK", "60"))
PIPELINE_SELECT_COUNT = int(os.environ.get("PIPELINE_SELECT_COUNT", "3"))

app = FastAPI(title="Tender Matching API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only one pipeline run at a time. This isn't just about not hammering the
# external API concurrently -- stage output is captured by temporarily
# redirecting the process's sys.stdout (see QueueWriter below), which is a
# global, so two pipelines running at once would interleave/scramble each
# other's progress messages.
PIPELINE_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# Loading the numbered workflow_tools scripts. Their filenames start with a
# digit, so they can't be `import`-ed normally -- same importlib pattern
# those scripts already use internally to load each other.
# ---------------------------------------------------------------------------

def load_module(name: str, path: Path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"required workflow script not found: {path}")
    # 2_company_details_to_initial_filter.py does `from common import
    # get_gemini_api_key`, a plain top-level import that only resolves if
    # its own folder is on sys.path.
    workflow_dir = str(path.parent)
    if workflow_dir not in sys.path:
        sys.path.insert(0, workflow_dir)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


filter_module = load_module("details_to_filter", FILTER_SCRIPT_PATH)
run_filter_module = load_module("run_filter_for_tenders", FETCH_FILTER_RUNNER_PATH)
standardize_module = load_module("standardize_tenders", STANDARDIZE_SCRIPT_PATH)
select_module = load_module("select_tenders", SELECT_SCRIPT_PATH)


def slugify(name: str) -> str:
    """Identical to fetch_tenders_oeffentlichevergabe.py's slugify(), so
    company keys line up across every stage."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# ---------------------------------------------------------------------------
# company_details.json persistence
# ---------------------------------------------------------------------------

def save_company_profile(profile: CompanyProfile) -> tuple[dict, int]:
    """Append the submitted CompanyProfile to company_details.json, in the
    same {"companies": [...]} shape 1_company_md_to_company_details.py
    produces. Returns (saved_record, total_companies_in_file)."""
    if COMPANY_DETAILS_PATH.exists():
        try:
            data = json.loads(COMPANY_DETAILS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}

    if "companies" not in data or not isinstance(data["companies"], list):
        data["companies"] = []

    record = profile.model_dump()
    record["submittedAt"] = datetime.now(timezone.utc).isoformat()

    data["companies"].append(record)

    COMPANY_DETAILS_PATH.parent.mkdir(parents=True, exist_ok=True)
    COMPANY_DETAILS_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return record, len(data["companies"])


# ---------------------------------------------------------------------------
# Progress streaming plumbing
# ---------------------------------------------------------------------------

class QueueWriter:
    """File-like object that forwards written lines to a queue.Queue as SSE
    progress events. Used via contextlib.redirect_stdout to capture the
    workflow scripts' existing print() calls in near-real time, without
    having to edit those scripts to accept a callback."""

    def __init__(self, q: "queue.Queue", stage: str):
        self._q = q
        self._stage = stage
        self._buffer = ""

    def write(self, text: str):
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.strip()
            if line:
                self._q.put({"type": "progress", "stage": self._stage, "message": line})

    def flush(self):
        pass


def run_stage(q: "queue.Queue", stage: str, label: str, fn, *args, **kwargs):
    """Emit a human-readable label, then run fn with its stdout captured
    into progress events tagged with `stage`. Converts the workflow
    scripts' sys.exit()-on-bad-input calls into a normal exception instead
    of killing the API process."""
    q.put({"type": "progress", "stage": stage, "message": label})
    writer = QueueWriter(q, stage)
    try:
        with contextlib.redirect_stdout(writer):
            return fn(*args, **kwargs)
    except SystemExit as e:
        raise RuntimeError(f"{label} -- {e}") from e


def format_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ---------------------------------------------------------------------------
# Turning a selected standardized tender + the submitted profile into a
# TenderMatch. No LLM call here -- the tender already passed the
# Gemini-generated filters.yaml block earlier in the pipeline; this is a
# deterministic explanation layer for the UI, not a second AI pass.
# ---------------------------------------------------------------------------

def _parse_amount(value) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").replace("€", "").strip())
    except (TypeError, ValueError):
        return None


def build_match(tender_dict: dict, profile: CompanyProfile) -> dict:
    tender = Tender(**tender_dict)

    reasons: list[str] = []
    considerations: list[str] = []
    score = 65

    vmin, vmax = _parse_amount(profile.contractValueMin), _parse_amount(profile.contractValueMax)
    if tender.value is not None and vmin is not None and vmax is not None:
        if vmin <= tender.value <= vmax:
            score += 15
            reasons.append("Contract value falls within your stated range.")
        else:
            considerations.append("Contract value falls outside your stated range -- double-check it fits.")
    elif tender.value is None:
        considerations.append("The buyer did not publish a contract value -- verify before bidding.")

    place = profile.placeOfPerformance or ""
    if place and tender.location:
        place_parts = [p.strip().lower() for p in re.split(r"[,/]", place) if p.strip()]
        if any(p in tender.location.lower() for p in place_parts):
            score += 10
            reasons.append("Located in or near your stated place of performance.")

    if tender.contractNature and profile.contractNature and tender.contractNature.lower() == profile.contractNature.lower():
        score += 5
        reasons.append("Contract nature matches your profile.")

    reasons.append("Passed the CPV, region and value filters generated from your company profile.")

    if tender.requiredCertificates:
        considerations.append("Requires certificate(s): " + ", ".join(tender.requiredCertificates))
    if tender.guaranteeRequired:
        considerations.append(f"Guarantee required: {tender.guaranteeRequired}")

    score = max(50, min(score, 97))

    title = tender.title or "This tender"
    authority = tender.authority or "the contracting authority"
    summary = (
        f"{title}, published by {authority}, was pulled in by the tender filter generated from "
        f"your company profile and is worth a closer look."
    )

    match = TenderMatch(
        tender=tender,
        score=score,
        reasons=reasons,
        considerations=considerations,
        summary=summary,
    )
    return match.model_dump()


# ---------------------------------------------------------------------------
# The pipeline itself
# ---------------------------------------------------------------------------

def run_pipeline(profile: CompanyProfile, q: "queue.Queue") -> list[dict]:
    q.put({"type": "progress", "stage": "starting", "message": "Starting your tender search..."})

    company_name = (
        f"Web submission {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} "
        f"({uuid.uuid4().hex[:6]})"
    )
    company_key = slugify(company_name)

    profile_data = profile.model_dump()
    profile_data["name"] = company_name
    enriched_profile = CompanyProfile(**profile_data)

    run_stage(
        q, "saving_profile", "Saving your company profile...",
        save_company_profile, enriched_profile,
    )

    filters_path = WORKFLOW_TOOLS_DIR / f".web_filters_{company_key}.yaml"
    try:
        run_stage(
            q, "building_filter",
            "Working out which tender categories and regions fit your company "
            "(this calls Gemini and can take a moment)...",
            filter_module.run,
            input_path=str(COMPANY_DETAILS_PATH),
            out_path=str(filters_path),
            companies=[company_name],
        )

        run_stage(
            q, "fetching_tenders",
            f"Searching oeffentlichevergabe.de for matching tenders "
            f"(up to {PIPELINE_MAX_DAYS_BACK} days back)...",
            run_filter_module.run_filter_for_tenders,
            filters_path=filters_path,
            company_details_path=COMPANY_DETAILS_PATH,
            fetch_module_path=FETCH_MODULE_PATH,
            output_dir=TENDERS_DIR,
            target=PIPELINE_TARGET_COUNT,
            max_days=PIPELINE_MAX_DAYS_BACK,
            companies=[company_key],
            force=True,  # single freshly-written ephemeral company; skip the batch cross-check
        )

        run_stage(
            q, "standardizing", "Standardizing the tenders we found...",
            standardize_module.standardize_tenders,
            input_dir=TENDERS_DIR,
            output_dir=STANDARDIZED_TENDERS_DIR,
            companies=[company_key],
        )

        q.put({"type": "progress", "stage": "selecting", "message": "Picking your top tenders..."})
        try:
            selected = select_module.select_tenders(
                company_key=company_key,
                count=PIPELINE_SELECT_COUNT,
                standardized_dir=STANDARDIZED_TENDERS_DIR,
            )
        except (FileNotFoundError, ValueError) as e:
            raise RuntimeError(
                "No tenders matched your profile within the search window. "
                "Try broadening your specifications or contract value range."
            ) from e
    finally:
        filters_path.unlink(missing_ok=True)

    q.put({"type": "progress", "stage": "done", "message": f"Found {len(selected)} tender(s)."})
    return [build_match(t, profile) for t in selected]


def pipeline_event_stream(profile: CompanyProfile):
    q: "queue.Queue" = queue.Queue()
    result: dict = {}

    def worker():
        try:
            with PIPELINE_LOCK:
                result["matches"] = run_pipeline(profile, q)
        except Exception as e:  # surfaced to the client as an error event, not a 500
            result["error"] = str(e)
        finally:
            q.put(None)  # sentinel: no more events

    threading.Thread(target=worker, daemon=True).start()

    while True:
        item = q.get()
        if item is None:
            break
        yield format_sse(item)

    if "error" in result:
        yield format_sse({"type": "error", "message": result["error"]})
    else:
        yield format_sse({"type": "done", "matches": result.get("matches", [])})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "companyDetailsPath": str(COMPANY_DETAILS_PATH.resolve()),
        "companyDetailsExists": COMPANY_DETAILS_PATH.exists(),
        "tendersDir": str(TENDERS_DIR.resolve()),
        "standardizedTendersDir": str(STANDARDIZED_TENDERS_DIR.resolve()),
        "pipeline": {
            "targetCount": PIPELINE_TARGET_COUNT,
            "maxDaysBack": PIPELINE_MAX_DAYS_BACK,
            "selectCount": PIPELINE_SELECT_COUNT,
        },
    }


@app.post("/admin/save-company-profile")
def save_company_profile_route(profile: CompanyProfile):
    """Writes the submitted profile to company_details.json directly,
    without running the rest of the pipeline -- for pre-registering real
    companies ahead of a scheduled/batch workflow_tools run."""
    record, total = save_company_profile(profile)
    return {
        "status": "saved",
        "path": str(COMPANY_DETAILS_PATH.resolve()),
        "totalCompanies": total,
        "record": record,
    }


@app.post("/tenders/match")
def match_tenders_stream(profile: CompanyProfile):
    """Runs the full live pipeline for this profile and streams progress
    back as Server-Sent Events, ending with one {"type": "done", "matches":
    [...]} event (or {"type": "error", ...} on failure)."""
    return StreamingResponse(
        pipeline_event_stream(profile),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx response buffering, if present
        },
    )