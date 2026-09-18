"""
backend/workflow_tools/tender_index.py

Shared helpers for reading/writing the per-company index.json that lives
at backend/tenders/<company_key>/index.json, alongside that company's raw
tender markdown files (<notice_id>.md, written by
fetch_tenders_oeffentlichevergabe.py). This replaces
4_standardize_tenders.py / backend/standardized_tenders/, which have been
removed -- backend/tenders/ is now the only tender store, and the raw
per-tender .md file is what gets sent to the frontend.

index.json shape:
{
  "updated_at": "<iso timestamp>",
  "tenders": {
    "<notice_id>": {
      "priority": 3,
      "first_seen_run": "<iso timestamp>",
      "last_seen_run": "<iso timestamp>",
      "selected_count": 0,
      "last_selected_at": null,
      "title": "...", "authority": "...", "value": 123.0,
      "currency": "EUR", "deadline": "2026-10-01"
    },
    ...
  }
}

PRIORITY RULES (see conversation with the user for the source of these):
  - A tender's notice_id doubles as its id everywhere (it's already the
    .md filename and release["id"]).
  - Every time 3_run_filter_for_tenders.py runs, every tender whose .md
    file is still on disk gets priority += 1. A tender seen for the first
    time this run starts at priority = 1 (not incremented an extra time in
    the same run).
  - 5_select_tenders.py picks the highest-priority tenders. Selecting a
    tender resets its priority back to 0 (see mark_selected()) so it
    doesn't just keep winning every future selection -- this half of the
    behavior wasn't explicitly specified, it's this module's assumption
    about how "select from the highest priority" should behave end-to-end.
    Flip it out easily if that's not what's wanted.
  - 6_user_select_remove_tenders.py marks a tender "removed" when the user
    dismisses it (see mark_removed()): its priority drops to
    REMOVED_PRIORITY (below anything a normal run would ever produce) and
    it's permanently excluded from pick_top(), so it can never be
    reselected. Unlike the "file no longer on disk" case below, a removed
    tender's index entry is deliberately KEPT (not deleted) as a seen/
    rejected history, even though its .md file has moved out to
    tenders_seen/<company_key>/ and is therefore no longer "on disk" from
    this module's point of view.
  - Any other index entry is dropped if its .md file is no longer present
    on disk (e.g. manually deleted, moved by something other than the
    removal flow above).

The cached metadata fields (title/authority/value/currency/deadline) are
NOT a replacement for the .md file -- they exist purely so something can
list/sort what's in the index without re-reading and re-parsing every raw
release JSON. The .md file's embedded OCDS JSON remains the single source
of truth.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

JSON_BLOCK_RE = re.compile(r"## Full raw release JSON\s*```json\s*(.*?)```", re.DOTALL)
INDEX_FILENAME = "index.json"

# Sentinel priority assigned to a removed/dismissed tender -- deliberately
# lower than anything a normal run could produce (new tenders start at 1,
# and mark_selected() floors out at 0), so a removed tender can never
# accidentally out-rank a live one even if pick_top()'s explicit
# `removed` check were ever bypassed.
REMOVED_PRIORITY = -1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def index_path(company_dir) -> Path:
    return Path(company_dir) / INDEX_FILENAME


def load_index(company_dir) -> dict:
    path = index_path(company_dir)
    if not path.exists():
        return {"tenders": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("tenders", {})
    return data


def save_index(company_dir, data: dict) -> None:
    data["updated_at"] = _now_iso()
    index_path(company_dir).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def extract_release_json(md_text: str) -> dict:
    match = JSON_BLOCK_RE.search(md_text)
    if not match:
        raise ValueError("no '## Full raw release JSON' fenced block found")
    return json.loads(match.group(1))


def _extract_value(release: dict):
    tender = release.get("tender", {}) or {}
    val = tender.get("value", {}) or {}
    amount, currency = val.get("amount"), val.get("currency")
    if amount is not None:
        return amount, currency
    total, found, lot_currency = 0.0, False, None
    for lot in tender.get("lots", []) or []:
        lv = lot.get("value") or {}
        if lv.get("amount") is not None:
            total += lv["amount"]
            lot_currency = lv.get("currency", lot_currency)
            found = True
    return (total, lot_currency) if found else (None, None)


def extract_metadata(release: dict) -> dict:
    """Cheap display metadata cached into index.json. See module docstring
    -- this is intentionally not the full standardized schema
    4_standardize_tenders.py used to build."""
    tender = release.get("tender", {}) or {}
    amount, currency = _extract_value(release)
    end_date = (tender.get("tenderPeriod", {}) or {}).get("endDate")
    return {
        "title": tender.get("title"),
        "authority": (release.get("buyer", {}) or {}).get("name"),
        "value": amount,
        "currency": currency,
        "deadline": end_date.split("T")[0] if isinstance(end_date, str) and end_date else None,
    }


def sync_index_with_folder(company_dir) -> dict:
    """Call after a fetch run for this company. Walks every <notice_id>.md
    currently in company_dir and:
      - adds any notice_id not yet indexed, at priority=1
      - bumps priority by 1 for every notice_id already indexed
      - refreshes cached metadata + last_seen_run for all of them
      - drops index entries whose .md file is no longer present
    Saves and returns the updated index dict.
    """
    company_dir = Path(company_dir)
    data = load_index(company_dir)
    tenders = data["tenders"]

    on_disk = {p.stem for p in company_dir.glob("*.md")}

    # Drop stale entries (file was removed/moved outside the removal flow
    # below) -- but NEVER drop a `removed` entry just because its .md file
    # is (by design) no longer in this folder; that's what distinguishes a
    # deliberately-removed tender from an orphaned index row.
    for stale_id in list(set(tenders) - on_disk):
        if not tenders[stale_id].get("removed"):
            del tenders[stale_id]

    now = _now_iso()
    for notice_id in sorted(on_disk):
        md_path = company_dir / f"{notice_id}.md"
        try:
            release = extract_release_json(md_path.read_text(encoding="utf-8"))
            metadata = extract_metadata(release)
        except Exception as e:
            metadata = {}
            print(f"    WARNING: could not extract index metadata for {notice_id}.md: {e}")

        if notice_id in tenders:
            entry = tenders[notice_id]
            entry["priority"] = entry.get("priority", 0) + 1
            entry["last_seen_run"] = now
            entry.update(metadata)
        else:
            tenders[notice_id] = {
                "priority": 1,
                "first_seen_run": now,
                "last_seen_run": now,
                "selected_count": 0,
                "last_selected_at": None,
                **metadata,
            }

    save_index(company_dir, data)
    return data


def pick_top(company_dir, count: int) -> list:
    """Up to `count` notice_ids, highest priority first, EXCLUDING anything
    marked removed (see mark_removed()). Ties are broken toward whichever
    has been selected least often, so a tender that's somehow tied at the
    top forever doesn't monopolize every selection."""
    data = load_index(company_dir)
    candidates = [
        (notice_id, entry) for notice_id, entry in data["tenders"].items()
        if not entry.get("removed")
    ]
    ranked = sorted(
        candidates,
        key=lambda kv: (-kv[1].get("priority", 0), kv[1].get("selected_count", 0)),
    )
    return [notice_id for notice_id, _entry in ranked[:count]]


def mark_selected(company_dir, notice_ids: list) -> None:
    """Call after 5_select_tenders.py picks. Bumps selected_count, stamps
    last_selected_at, and resets priority to 0 -- see module docstring."""
    data = load_index(company_dir)
    tenders = data["tenders"]
    now = _now_iso()
    for notice_id in notice_ids:
        if notice_id in tenders:
            entry = tenders[notice_id]
            entry["selected_count"] = entry.get("selected_count", 0) + 1
            entry["last_selected_at"] = now
            entry["priority"] = 0
    save_index(company_dir, data)


def mark_removed(company_dir, notice_id: str) -> None:
    """Call after 6_user_select_remove_tenders.py moves a tender's .md file
    out to tenders_seen/<company_key>/. Marks the index entry removed
    (kept, not deleted -- see module docstring) and floors its priority so
    pick_top() never surfaces it again even as a fallback.

    Raises KeyError if notice_id isn't in the index at all (the caller is
    expected to have already confirmed the tender existed before moving
    its file).
    """
    data = load_index(company_dir)
    tenders = data["tenders"]
    if notice_id not in tenders:
        raise KeyError(f"'{notice_id}' not found in index.json for {company_dir}")
    entry = tenders[notice_id]
    entry["removed"] = True
    entry["removed_at"] = _now_iso()
    entry["priority"] = REMOVED_PRIORITY
    save_index(company_dir, data)