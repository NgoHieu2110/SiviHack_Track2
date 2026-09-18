"""
backend/oeffentlichevergabe/inspect_release.py

DIAGNOSTIC TOOL - not part of the normal fetch_tenders_oeffentlichevergabe.py pipeline.

Fetches ONE day of notices from the Bekanntmachungsservice OCDS export,
grabs the first release found (or a specific notice ID if given), and
writes out a markdown file containing:

  1. The full raw OCDS release JSON, pretty-printed, so you can see every
     field actually present on a real notice (not just the ~4 fields
     fetch_tenders_oeffentlichevergabe.py currently extracts).
  2. A "field inventory" checklist that specifically flags whether the
     richer OCDS/eForms fields discussed as candidates for filters.yaml
     (lots, otherRequirements, additionalClassifications, procurementMethod,
     tenderPeriod, parties[].roles, etc.) are actually populated on this
     release or not - so you can tell what's realistically usable vs. what
     is present in the schema but rarely filled in by this data source.

This intentionally does NOT touch filters.yaml, company_profiles.py, or
fetch_tenders_oeffentlichevergabe.py. It's read-only reconnaissance to decide what's worth
wiring into the real matching logic afterward.

Usage:
    python inspect_release.py                        # first release of yesterday
    python inspect_release.py --day 2024-06-15        # first release of a specific day
    python inspect_release.py --day 2024-06-15 --notice-id abc-123   # a specific notice
    python inspect_release.py --out my_sample.md      # custom output path
"""
import argparse
import io
import json
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import requests

API_URL = "https://oeffentlichevergabe.de/api/notice-exports"
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUT = SCRIPT_DIR / "sample_release.md"

# NOTE: this used to be a curated shortlist of "fields worth checking"
# (tender.lots, tender.otherRequirements, etc). The inventory table below now
# walks the ENTIRE release recursively instead, so every field actually
# present on the notice shows up - not just a hand-picked subset.


def flatten_paths(obj, prefix=""):
    """Recursively walk obj and return a list of (path, value) pairs for
    every leaf (non-dict, non-list) value, plus explicit entries for empty
    dicts/lists so those aren't silently skipped. List indices are rendered
    as [i] in the path."""
    rows = []
    if isinstance(obj, dict):
        if not obj:
            rows.append((prefix or "(root)", None, "_(empty object)_"))
            return rows
        for key, val in obj.items():
            child_path = f"{prefix}.{key}" if prefix else key
            rows.extend(flatten_paths(val, child_path))
    elif isinstance(obj, list):
        if not obj:
            rows.append((prefix, None, "_(empty list)_"))
            return rows
        for i, item in enumerate(obj):
            rows.extend(flatten_paths(item, f"{prefix}[{i}]"))
    else:
        rows.append((prefix, obj, None))
    return rows


def summarize_value(val, max_len=300):
    """Short one-line-ish preview of a field's value for the inventory table."""
    if val is None:
        return "_(present but null)_"
    if isinstance(val, bool):
        return f"`{val}`"
    if isinstance(val, (int, float)):
        return f"`{val}`"
    if isinstance(val, str):
        s = val.strip().replace("\n", " ")
        return (s[:max_len] + "...") if len(s) > max_len else (s or "_(empty string)_")
    if isinstance(val, list):
        if not val:
            return "_(empty list)_"
        return f"list of {len(val)} item(s), first: `{json.dumps(val[0], ensure_ascii=False)[:max_len]}`"
    if isinstance(val, dict):
        keys = ", ".join(val.keys())
        return f"object with keys: `{keys}`"
    return str(val)


def fetch_day_first_matching_release(pub_day: str, wanted_notice_id: str | None):
    """Download one day's OCDS export, return (release, source_filename) for
    either the first release found, or the one matching wanted_notice_id."""
    print(f"Fetching {pub_day}...", flush=True)
    resp = requests.get(
        API_URL, params={"pubDay": pub_day, "format": "ocds.zip"}, timeout=60
    )
    if resp.status_code == 400:
        sys.exit(f"400 Bad Request for {pub_day} - likely out of the API's valid "
                  f"date range (before 2022-12-01, or today/future). Try another day.")
    resp.raise_for_status()

    try:
        archive = zipfile.ZipFile(io.BytesIO(resp.content))
    except zipfile.BadZipFile:
        sys.exit(f"Response for {pub_day} was not a valid ZIP (empty day or error page). "
                  f"Try a different --day.")

    json_files = sorted(n for n in archive.namelist() if n.endswith(".json"))
    print(f"  {len(json_files)} notice files in this day's export.")
    if not json_files:
        sys.exit(f"No notices published on {pub_day}. Try a different --day.")

    for fname in json_files:
        with archive.open(fname) as f:
            data = json.loads(f.read().decode("utf-8"))
        for release in data.get("releases", []):
            if wanted_notice_id is None or release.get("id") == wanted_notice_id:
                return release, fname

    if wanted_notice_id:
        sys.exit(f"Notice ID '{wanted_notice_id}' not found in {pub_day}'s export "
                  f"({len(json_files)} files checked).")
    sys.exit(f"No releases found inside any notice file for {pub_day} (unexpected - "
              f"the files were non-empty JSON but contained no 'releases' array).")


def render_markdown(release, pub_day, source_fname):
    lines = []
    lines.append(f"# Sample OCDS release — {pub_day}")
    lines.append("")
    lines.append(f"- **Source day:** {pub_day}")
    lines.append(f"- **Source file in ZIP:** `{source_fname}`")
    lines.append(f"- **Notice ID:** `{release.get('id', 'unknown')}`")
    lines.append(f"- **OCID:** `{release.get('ocid', 'unknown')}`")
    lines.append(f"- **Title:** {release.get('tender', {}).get('title', 'N/A')}")
    lines.append("")
    lines.append(
        "This file is diagnostic output from `inspect_release.py`, generated to "
        "check which OCDS/eForms fields are actually populated on real "
        "Bekanntmachungsservice notices before deciding what to add to "
        "`filters.yaml` / `company_profiles.py`. It is not consumed by "
        "`fetch_tenders.py`."
    )
    lines.append("")

    # --- Field inventory ---------------------------------------------------
    lines.append("## Field inventory (every field present on this release)")
    lines.append("")
    lines.append(
        "Full recursive walk of the release — every leaf field actually "
        "present, not just a hand-picked subset. A field missing here might "
        "still appear on other notices, so check a few more samples with "
        "different `--day` / `--notice-id` values before ruling anything "
        "out or building a filter around it."
    )
    lines.append("")
    lines.append("| Field (path) | Value |")
    lines.append("|---|---|")
    for path, val, precomputed_status in flatten_paths(release):
        status = precomputed_status if precomputed_status is not None else summarize_value(val)
        lines.append(f"| `{path}` | {status} |")
    lines.append("")

    # --- Currently-used fields, for comparison ------------------------------
    lines.append("## Fields fetch_tenders.py currently reads")
    lines.append("")
    lines.append(
        "For comparison — these are the only fields the current matching "
        "logic (`get_release_cpvs`, `get_release_regions`, "
        "`get_release_value`, `get_release_text_blob` in `fetch_tenders.py`) "
        "actually looks at:"
    )
    lines.append("")
    lines.append("- `tender.items[].classification.id` (CPV codes)")
    lines.append("- `tender.items[].deliveryAddress.region`, `buyer.address.region`, "
                  "`parties[].address.region` (NUTS codes)")
    lines.append("- `tender.value.amount` / `tender.value.currency`, falling back to "
                  "summed `tender.lots[].value`")
    lines.append("- `tender.title`, `tender.description`, "
                  "`tender.procurementMethodRationale`, `tender.lots[].title`, "
                  "`tender.lots[].description` (as one lowercased text blob for "
                  "keyword matching)")
    lines.append("")

    # --- Full raw JSON -------------------------------------------------------
    lines.append("## Full raw release JSON")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(release, indent=2, ensure_ascii=False))
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--day", type=str, default=None,
                         help="YYYY-MM-DD to fetch. Defaults to yesterday.")
    parser.add_argument("--notice-id", type=str, default=None,
                         help="Specific notice ID to extract. Defaults to the first release found.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                         help=f"Output markdown path (default: {DEFAULT_OUT}).")
    args = parser.parse_args()

    pub_day = args.day or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    release, source_fname = fetch_day_first_matching_release(pub_day, args.notice_id)
    md = render_markdown(release, pub_day, source_fname)

    args.out.write_text(md, encoding="utf-8")
    print(f"\nWrote sample release to: {args.out}")
    print(f"Notice ID: {release.get('id', 'unknown')}")
    print(f"Title: {release.get('tender', {}).get('title', 'N/A')}")


if __name__ == "__main__":
    main()