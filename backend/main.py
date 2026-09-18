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
This backend is configured for a single company -- there is no per-visitor
company_key or live-search isolation. POST /tenders/match runs the *entire*
workflow pipeline live, for the one company profile just submitted, and
streams progress back to the browser as Server-Sent Events
(`text/event-stream`) over the same POST response body:

    1. Overwrite company_details.json with the submitted profile (a single
       flat object -- see 1_company_md_to_company_details.py's schema for
       context). Submitting a new profile replaces whatever company was
       there before.
    2. workflow_tools/2_company_details_to_initial_filter.py: ask Gemini to
       turn that profile into filters.yaml (CPV/NUTS prefixes, value range,
       exclusions, role hints).
    3. workflow_tools/3_run_filter_for_tenders.py: walk oeffentlichevergabe.de
       backward day by day until PIPELINE_TARGET_COUNT tenders match, or
       PIPELINE_MAX_DAYS_BACK is hit. This also updates
       backend/tenders/index.json (priority bookkeeping -- see
       tender_index.py).
    4. workflow_tools/7_select_from_raw_tenders.py: ask Gemini to pick and
       explain PIPELINE_SELECT_COUNT of the raw matched tenders in
       backend/tenders/ for this company profile, returning each one's
       full match record (including raw markdown) directly -- there is no
       separate build_match() scoring step anymore, this stage returns the
       finished match objects.

    There is no more standardization stage -- backend/standardized_tenders/
    and 4_standardize_tenders.py have been removed. backend/tenders/ is now
    the only tender store, and what's sent to the frontend is each selected
    tender's raw .md content rather than a parsed/standardized JSON record.

PIPELINE_LOCK serializes /tenders/match, /tenders/remove and /tenders/refine
calls (see its own comment below) -- since there's only one shared
company_details.json / filters.yaml / tenders/ store, concurrent
submissions would otherwise step on each other's state rather than just
being slow.

Each SSE event is one line of JSON after "data: ":
    {"type": "progress", "stage": "...", "message": "..."}   (many)
    {"type": "done", "matches": [...]}                         (one, on success)
    {"type": "error", "message": "..."}                        (one, on failure)

This is a genuinely slow, external-API-bound operation (a Gemini call plus
however many days of oeffentlichevergabe.de fetches it takes), which is why
it streams progress rather than returning a single blocking JSON response.

Also exposes POST /admin/save-company-profile, which writes whatever
CompanyProfile is POSTed to it into company_details.json directly, without
running the rest of the pipeline -- useful for updating the company profile
that a scheduled/batch run of workflow_tools 2-3-7 will pick up later,
without immediately kicking off a live fetch.

POST /tenders/refine handles the "kept 2 of 3, dismissed 1" case: it
computes a new per-criterion filter tolerance from that choice (see
workflow_tools/8_change_filter_tolerance.py), dismisses the removed tender,
rewrites filters.yaml, re-runs the fetch, and returns a single replacement
tender. NOTE: as of this merge, the replacement-picking step inside
8_change_filter_tolerance.py still calls the older
workflow_tools/5_select_tenders.py (priority-based) rather than
7_select_from_raw_tenders.py (AI-based) -- see that script's docstring for
why, and update it once 7_select_from_raw_tenders.py's signature is
available.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import queue
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402

from models import CompanyProfile  # noqa: E402
from pydantic import BaseModel  # noqa: E402

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
#       5_select_tenders.py
#       tender_index.py
#       company_details.json
#       filters.yaml
#     tenders/                     <- raw fetch output + index.json
#     tenders_seen/                <- dismissed tenders
#
# Every path is overridable via env var if your layout differs.
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
WORKFLOW_TOOLS_DIR = Path(os.environ.get("WORKFLOW_TOOLS_DIR", BASE_DIR / "workflow_tools"))
FETCH_MODULE_PATH = Path(
    os.environ.get("FETCH_MODULE_PATH", BASE_DIR / "oeffentlichevergabe" / "fetch_tenders_oeffentlichevergabe.py")
)
COMPANY_DETAILS_PATH = Path(os.environ.get("COMPANY_DETAILS_PATH", WORKFLOW_TOOLS_DIR / "company_details.json"))
FILTERS_PATH = Path(os.environ.get("FILTERS_PATH", WORKFLOW_TOOLS_DIR / "filters.yaml"))
TENDERS_DIR = Path(os.environ.get("TENDERS_DIR", BASE_DIR / "tenders"))
TENDERS_SEEN_DIR = Path(os.environ.get("TENDERS_SEEN_DIR", BASE_DIR / "tenders_seen"))

FILTER_SCRIPT_PATH = Path(os.environ.get("FILTER_SCRIPT_PATH", WORKFLOW_TOOLS_DIR / "2_company_details_to_initial_filter.py"))
FETCH_FILTER_RUNNER_PATH = Path(os.environ.get("FETCH_FILTER_RUNNER_PATH", WORKFLOW_TOOLS_DIR / "3_run_filter_for_tenders.py"))
#SELECT_SCRIPT_PATH = Path(os.environ.get("SELECT_SCRIPT_PATH", WORKFLOW_TOOLS_DIR / "5_select_tenders.py"))
REMOVE_SCRIPT_PATH = Path(os.environ.get("REMOVE_SCRIPT_PATH", WORKFLOW_TOOLS_DIR / "6_user_select_remove_tenders.py"))
SELECT_FROM_RAW_SCRIPT_PATH = Path(os.environ.get("SELECT_FROM_RAW_SCRIPT_PATH", WORKFLOW_TOOLS_DIR / "7_select_from_raw_tenders.py"))
CHANGE_TOLERANCE_SCRIPT_PATH = Path(os.environ.get("CHANGE_TOLERANCE_SCRIPT_PATH", WORKFLOW_TOOLS_DIR / "8_change_filter_tolerance.py"))

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# How many tenders the fetch stage tries to collect before we pick
# PIPELINE_SELECT_COUNT of them, how many days back it's allowed to walk to
# get there, and how many we finally show. Kept small by default since this
# now runs live, in the request path.
PIPELINE_TARGET_COUNT = int(os.environ.get("PIPELINE_TARGET_COUNT", "3"))
PIPELINE_MAX_DAYS_BACK = int(os.environ.get("PIPELINE_MAX_DAYS_BACK", "5"))
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
# other's progress messages. It also protects the single shared
# company_details.json / filters.yaml / tenders/ store from being read and
# written by two requests at once.
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
#select_module = load_module("select_tenders", SELECT_SCRIPT_PATH)
remove_module = load_module("user_select_remove_tenders", REMOVE_SCRIPT_PATH)
select_from_raw_module = load_module("select_from_raw", SELECT_FROM_RAW_SCRIPT_PATH)
change_tolerance_module = load_module("change_filter_tolerance", CHANGE_TOLERANCE_SCRIPT_PATH)

# How many new candidates the re-fetch inside /tenders/refine tries to
# collect (and how far back it's allowed to walk) before
# change_filter_tolerance() picks the single replacement tender. Kept
# small/fast, same reasoning as PIPELINE_TARGET_COUNT/MAX_DAYS_BACK above.
REFINE_TARGET_COUNT = int(os.environ.get("REFINE_TARGET_COUNT", "6"))
REFINE_MAX_DAYS_BACK = int(os.environ.get("REFINE_MAX_DAYS_BACK", "60"))

# ---------------------------------------------------------------------------
# company_details.json persistence
# ---------------------------------------------------------------------------

def save_company_profile(profile: CompanyProfile) -> dict:
    """Writes the submitted CompanyProfile to company_details.json as a
    single flat object, overwriting whatever was there before -- there is
    only one company per backend instance, not a list. Returns the saved
    record."""
    record = profile.model_dump()
    record["submittedAt"] = datetime.now(timezone.utc).isoformat()

    COMPANY_DETAILS_PATH.parent.mkdir(parents=True, exist_ok=True)
    COMPANY_DETAILS_PATH.write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return record


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
# Turning a selected tender + the submitted profile into a match record for
# the frontend.
#
# PLACEHOLDER, PENDING REDESIGN: the old version of this built a 50-97 score
# and reasons/considerations off standardized fields (tender.value,
# tender.location, tender.contractNature, tender.requiredCertificates, ...)
# that came from 4_standardize_tenders.py. That stage is gone -- a selected
# tender is now just {id, title, authority, value, currency, deadline,
# priority, markdown} (see 5_select_tenders.py) -- so most of that scoring
# logic no longer has inputs to work with. Scoring/reasons are intentionally
# left minimal here until that's redesigned; this just passes the raw
# markdown through with a couple of cached display fields on top.
# No LLM call here either way -- the tender already passed the
# Gemini-generated filters.yaml block earlier in the pipeline.
# ---------------------------------------------------------------------------

def build_match(tender_dict: dict, profile: CompanyProfile) -> dict:
    title = tender_dict.get("title") or "This tender"
    authority = tender_dict.get("authority") or "the contracting authority"

    return {
        "tender": tender_dict,  # includes "markdown": full raw tender .md content
        "score": None,  # TODO: redesign now that standardized fields are gone
        "reasons": ["Passed the CPV, region and value filters generated from your company profile."],
        "considerations": [],
        "summary": (
            f"{title}, published by {authority}, was pulled in by the tender filter "
            f"generated from your company profile and is worth a closer look."
        ),
    }


# ---------------------------------------------------------------------------
# The pipeline itself
# ---------------------------------------------------------------------------

def run_pipeline(profile: CompanyProfile, q: "queue.Queue") -> list[dict]:
    q.put({"type": "progress", "stage": "selecting", "message": "Asking Gemini to pick and explain your top tenders..."})

    run_stage(
        q, "saving_profile", "Saving your company profile...",
        save_company_profile, profile,
    )

    run_stage(
        q, "building_filter",
        "Working out which tender categories and regions fit your company "
        "(this calls Gemini and can take a moment)...",
        filter_module.run,
        input_path=str(COMPANY_DETAILS_PATH),
        out_path=str(FILTERS_PATH),
    )

    run_stage(
        q, "fetching_tenders",
        f"Searching oeffentlichevergabe.de for matching tenders "
        f"(up to {PIPELINE_MAX_DAYS_BACK} days back)...",
        run_filter_module.run_filter_for_tenders,
        filters_path=FILTERS_PATH,
        fetch_module_path=FETCH_MODULE_PATH,
        output_dir=TENDERS_DIR,
        tenders_seen_dir=TENDERS_SEEN_DIR,
        target=PIPELINE_TARGET_COUNT,
        max_days=PIPELINE_MAX_DAYS_BACK,
    )

    q.put({"type": "progress", "stage": "selecting", "message": "Picking your top tenders..."})
    try:
        matches = select_from_raw_module.select_tenders_with_ai_from_raw(
            profile=profile.model_dump(),
            count=PIPELINE_SELECT_COUNT,
            raw_dir=TENDERS_DIR,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        raise RuntimeError(f"Could not select your top tenders: {e}") from e

    q.put({"type": "progress", "stage": "done", "message": f"Found {len(matches)} tender(s)."})
    return matches


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
        yield format_sse({
            "type": "done",
            "matches": result.get("matches", []),
        })


# ---------------------------------------------------------------------------
# Removing a tender the user dismissed. Much shorter than the match
# pipeline (no external API calls) but follows the same
# progress-over-SSE + single-lock pattern for consistency, and because
# run_stage()'s stdout capture is process-global (see PIPELINE_LOCK's own
# comment) -- a removal running concurrently with a match pipeline would
# scramble both their progress streams otherwise.
# ---------------------------------------------------------------------------

class RemoveTenderRequest(BaseModel):
    markdown: str  # full raw tender markdown, as returned by /tenders/match's
                    # "matches"[i].tender.markdown -- notice_id is extracted
                    # from it server-side, see 6_user_select_remove_tenders.py


def run_remove_pipeline(req: RemoveTenderRequest, q: "queue.Queue") -> dict:
    q.put({"type": "progress", "stage": "starting", "message": "Removing tender..."})
    try:
        result = run_stage(
            q, "removing",
            "Moving this tender out of your active tender list...",
            remove_module.remove_tender,
            markdown=req.markdown,
            tenders_dir=TENDERS_DIR,
            tenders_seen_dir=TENDERS_SEEN_DIR,
        )
    except (FileNotFoundError, ValueError) as e:
        raise RuntimeError(f"Could not remove tender: {e}") from e
    q.put({"type": "progress", "stage": "done", "message": "Tender removed."})
    return result


def remove_event_stream(req: RemoveTenderRequest):
    q: "queue.Queue" = queue.Queue()
    result: dict = {}

    def worker():
        try:
            with PIPELINE_LOCK:
                result["removal"] = run_remove_pipeline(req, q)
        except Exception as e:
            result["error"] = str(e)
        finally:
            q.put(None)

    threading.Thread(target=worker, daemon=True).start()

    while True:
        item = q.get()
        if item is None:
            break
        yield format_sse(item)

    if "error" in result:
        yield format_sse({"type": "error", "message": result["error"]})
    else:
        yield format_sse({"type": "done", **result.get("removal", {})})


# ---------------------------------------------------------------------------
# Refining the match set: the user kept 2 of the 3 tenders they were shown
# and dismissed the third. Nudges each filter criterion's tolerance toward
# the kept tenders and away from the removed one (see
# 8_change_filter_tolerance.py for the formula), re-runs the fetch at the
# new tolerance, and returns exactly one replacement tender. Follows the
# same progress-over-SSE + single-lock pattern as the other two pipelines,
# for the same reasons (stdout capture is process-global; all three share
# company_details.json / filters.yaml / tenders/).
#
# NOTE: the replacement tender is currently picked by
# 8_change_filter_tolerance.py's own call to 5_select_tenders.py
# (priority-based), not 7_select_from_raw_tenders.py (AI-based, used by the
# main /tenders/match pipeline above). Once 7_select_from_raw_tenders.py's
# signature is available this should probably be unified so /tenders/match
# and /tenders/refine pick tenders the same way.
# ---------------------------------------------------------------------------

class RefineTendersRequest(BaseModel):
    # Exactly 3 full raw tender markdown strings, as returned by a prior
    # /tenders/match "done" event's matches[i].tender.markdown -- the same
    # set the user was shown and chose 2 of 3 to keep.
    tenders: list[str]
    # 0-based index into `tenders` of the one the user dismissed. Matching
    # by position (not by re-comparing markdown content) is deliberate --
    # see 8_change_filter_tolerance.py's module docstring.
    removed_index: int
    # Optional override of the change constant k (see
    # 8_change_filter_tolerance.py). Omitted -> that script's own default.
    k: float | None = None


def run_refine_pipeline(req: RefineTendersRequest, q: "queue.Queue") -> dict:
    if len(req.tenders) != 3:
        raise RuntimeError(f"expected exactly 3 tenders, got {len(req.tenders)}")
    if req.removed_index not in (0, 1, 2):
        raise RuntimeError(f"removed_index must be 0, 1, or 2, got {req.removed_index}")

    q.put({"type": "progress", "stage": "starting", "message": "Refining your tender search..."})

    kwargs = dict(
        tenders=req.tenders,
        removed_index=req.removed_index,
        company_details_path=COMPANY_DETAILS_PATH,
        filters_path=FILTERS_PATH,
        fetch_module_path=FETCH_MODULE_PATH,
        tenders_dir=TENDERS_DIR,
        tenders_seen_dir=TENDERS_SEEN_DIR,
        target=REFINE_TARGET_COUNT,
        max_days=REFINE_MAX_DAYS_BACK,
    )
    if req.k is not None:
        kwargs["k"] = req.k

    try:
        result = run_stage(
            q, "refining",
            "Comparing what you kept against what you dismissed and "
            "re-tuning your filter...",
            change_tolerance_module.change_filter_tolerance,
            **kwargs,
        )
    except (FileNotFoundError, ValueError) as e:
        raise RuntimeError(f"Could not refine tenders: {e}") from e

    if result.get("replacement") is None:
        q.put({"type": "progress", "stage": "done",
               "message": "Filter updated, but no replacement tender matched within the search window."})
    else:
        q.put({"type": "progress", "stage": "done", "message": "Found a replacement tender."})
    return result


def refine_event_stream(req: RefineTendersRequest):
    q: "queue.Queue" = queue.Queue()
    result: dict = {}

    def worker():
        try:
            with PIPELINE_LOCK:
                result["refine"] = run_refine_pipeline(req, q)
        except Exception as e:
            result["error"] = str(e)
        finally:
            q.put(None)

    threading.Thread(target=worker, daemon=True).start()

    while True:
        item = q.get()
        if item is None:
            break
        yield format_sse(item)

    if "error" in result:
        yield format_sse({"type": "error", "message": result["error"]})
    else:
        yield format_sse({"type": "done", **result.get("refine", {})})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "companyDetailsPath": str(COMPANY_DETAILS_PATH.resolve()),
        "companyDetailsExists": COMPANY_DETAILS_PATH.exists(),
        "filtersPath": str(FILTERS_PATH.resolve()),
        "tendersDir": str(TENDERS_DIR.resolve()),
        "tendersSeenDir": str(TENDERS_SEEN_DIR.resolve()),
        "pipeline": {
            "targetCount": PIPELINE_TARGET_COUNT,
            "maxDaysBack": PIPELINE_MAX_DAYS_BACK,
            "selectCount": PIPELINE_SELECT_COUNT,
        },
        "refine": {
            "targetCount": REFINE_TARGET_COUNT,
            "maxDaysBack": REFINE_MAX_DAYS_BACK,
        },
    }


@app.post("/admin/save-company-profile")
def save_company_profile_route(profile: CompanyProfile):
    """Writes the submitted profile to company_details.json directly,
    without running the rest of the pipeline -- for updating the company
    profile ahead of a scheduled/batch workflow_tools run. Overwrites
    whatever company profile was previously stored."""
    record = save_company_profile(profile)
    return {
        "status": "saved",
        "path": str(COMPANY_DETAILS_PATH.resolve()),
        "record": record,
    }


@app.post("/tenders/match")
def match_tenders_stream(profile: CompanyProfile):
    """Runs the full live pipeline for this profile and streams progress
    back as Server-Sent Events, ending with one {"type": "done", "matches":
    [...]} event (or {"type": "error", ...} on failure). Submitting a
    profile overwrites the currently stored company_details.json/
    filters.yaml -- this backend only ever tracks one company."""
    return StreamingResponse(
        pipeline_event_stream(profile),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx response buffering, if present
        },
    )


@app.post("/tenders/remove")
def remove_tender_stream(req: RemoveTenderRequest):
    """Dismisses one tender (by its full raw markdown, from a prior
    /tenders/match "done" event's matches[i].tender.markdown) and streams
    progress back as Server-Sent Events, ending with one {"type": "done",
    "status": "removed" | "already_removed", "id": "..."} event (or
    {"type": "error", ...} on failure -- e.g. unparseable markdown or an
    unknown id). The notice_id is extracted from the markdown server-side,
    not supplied by the caller -- see 6_user_select_remove_tenders.py."""
    return StreamingResponse(
        remove_event_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/tenders/refine")
def refine_tenders_stream(req: RefineTendersRequest):
    """The user kept 2 of the 3 tenders from a prior /tenders/match and
    dismissed the third. Computes a new per-criterion filter tolerance from
    that choice, dismisses the removed tender (same effect as
    /tenders/remove), rewrites filters.yaml, re-runs the fetch, and returns
    ONE replacement tender to slot in where the dismissed one was. Streams
    progress as Server-Sent Events, ending with one {"type": "done",
    "removed": {...}, "new_tolerance": {...}, "replacement": {...} | null}
    event (or {"type": "error", ...} on failure). See
    8_change_filter_tolerance.py for the formula and full flow."""
    return StreamingResponse(
        refine_event_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )