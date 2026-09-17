"""
webscrape/fetch_tenders.py

Fetch German public tenders from oeffentlichevergabe.de and sort them into
per-company markdown files based on hard filters (CPV prefix, NUTS region,
value range, exclusion keywords).

Filters are NOT hardcoded in this file. They live in filters.yaml (next to
this script), which you edit directly (plain YAML, no Python) to fine-tune
matching per company.

For each company block in filters.yaml, this walks backward day by day from
yesterday until it has collected TARGET_COUNT matching tenders (or hits
MAX_DAYS_BACK), writing one markdown file per matching tender into:

    tenders/<company_slug>/<notice_id>.md

Each run starts by DELETING each company's existing output folder (the .md
files and the .seen_ids.txt tracker) and rebuilding it from scratch. This
means every run is a full fresh pull against today's filters.yaml, not an
incremental top-up — so re-running after loosening a filter won't leave
stale matches from a stricter previous run mixed in.

Usage:
    python fetch_tenders.py
    python fetch_tenders.py --target 40 --max-days 90
    python fetch_tenders.py --companies brenner_sohn_tiefbau
    python fetch_tenders.py --filters my_filters.yaml

filters.yaml is resolved relative to this script's own location, so it works
regardless of which directory you run the command from.
"""
import argparse
import io
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import requests
import yaml

API_URL = "https://oeffentlichevergabe.de/api/notice-exports"
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = SCRIPT_DIR / "tenders"
DEFAULT_FILTERS_PATH = SCRIPT_DIR / "filters.yaml"

DEFAULT_TARGET_COUNT = 40
DEFAULT_MAX_DAYS_BACK = 180  # safety cap so a bad filter config can't loop forever

REQUIRED_FIELDS = ["display_name", "cpv_prefixes", "nuts_prefixes"]


def load_companies(filters_path: Path) -> dict:
    """Load and lightly validate the company filter blocks from filters.yaml."""
    if not filters_path.exists():
        sys.exit(f"Filter file not found: {filters_path}\n"
                  f"Expected a YAML file with one block per company (see filters.yaml).")

    with open(filters_path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            sys.exit(f"Could not parse {filters_path} as YAML: {e}")

    if not isinstance(data, dict) or not data:
        sys.exit(f"{filters_path} must contain at least one company block "
                  f"(top-level YAML mapping of company_key -> filter fields).")

    companies = {}
    for key, profile in data.items():
        if not isinstance(profile, dict):
            sys.exit(f"Company '{key}' in {filters_path} must be a mapping, "
                      f"got {type(profile).__name__}.")
        missing = [f for f in REQUIRED_FIELDS if f not in profile or profile[f] in (None, [])]
        if missing:
            sys.exit(f"Company '{key}' in {filters_path} is missing required "
                      f"field(s): {', '.join(missing)}")
        profile.setdefault("value_min", None)
        profile.setdefault("value_max", None)
        profile.setdefault("exclude_keywords", [])
        profile.setdefault("role_hint_reject", [])
        profile.setdefault("notes", "")
        companies[key] = profile

    return companies


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def fetch_day_releases(pub_day: str):
    """Download one day's OCDS export and yield (release, source_filename)."""
    print(f"  Fetching {pub_day}...", flush=True)
    try:
        resp = requests.get(
            API_URL, params={"pubDay": pub_day, "format": "ocds.zip"}, timeout=60
        )
    except requests.exceptions.RequestException as e:
        print(f"    Request failed: {e}")
        return

    if resp.status_code == 400:
        # Out of valid range (before 2022-12-01, or today/future) - stop walking.
        print(f"    400 Bad Request for {pub_day} (likely out of valid date range). Stopping.")
        raise StopIteration

    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"    HTTP error: {e}")
        return

    try:
        archive = zipfile.ZipFile(io.BytesIO(resp.content))
    except zipfile.BadZipFile:
        print(f"    Not a valid ZIP for {pub_day} (empty day or error page). Skipping.")
        return

    json_files = [n for n in archive.namelist() if n.endswith(".json")]
    print(f"    {len(json_files)} notice files.")

    for fname in json_files:
        try:
            with archive.open(fname) as f:
                data = json.loads(f.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        for release in data.get("releases", []):
            yield release, fname


def get_release_cpvs(release):
    tender = release.get("tender", {})
    return [
        item.get("classification", {}).get("id", "")
        for item in tender.get("items", [])
        if item.get("classification", {}).get("id")
    ]


def get_release_regions(release):
    """Collect every NUTS region code we can find: item delivery addresses,
    buyer address, procuring entity's party address (if present in parties[])."""
    regions = set()
    tender = release.get("tender", {})

    for item in tender.get("items", []):
        region = item.get("deliveryAddress", {}).get("region")
        if region:
            regions.add(region)

    buyer_region = release.get("buyer", {}).get("address", {}).get("region")
    if buyer_region:
        regions.add(buyer_region)

    for party in release.get("parties", []):
        region = party.get("address", {}).get("region")
        if region:
            regions.add(region)

    return regions


def get_release_value(release):
    """Prefer tender.value; fall back to summing lot values if missing."""
    tender = release.get("tender", {})
    val = tender.get("value", {})
    amount = val.get("amount")
    currency = val.get("currency")
    if amount is not None:
        return amount, currency

    lots = tender.get("lots", [])
    total = 0.0
    found = False
    lot_currency = None
    for lot in lots:
        lv = lot.get("value", {})
        if lv.get("amount") is not None:
            total += lv["amount"]
            lot_currency = lv.get("currency", lot_currency)
            found = True
    if found:
        return total, lot_currency
    return None, None


def get_release_text_blob(release):
    tender = release.get("tender", {})
    parts = [
        tender.get("title", ""),
        tender.get("description", ""),
        tender.get("procurementMethodRationale", ""),
    ]
    for lot in tender.get("lots", []):
        parts.append(lot.get("title", ""))
        parts.append(lot.get("description", ""))
    return " \n".join(parts).lower()


def matches_profile(release, profile):
    """Hard filter: CPV prefix AND region prefix AND value in range,
    minus exclusion/role-hint keywords. Returns (bool, reason_str).

    DIAGNOSTIC NOTE (see filters.yaml header for the full write-up):
    every rejection path below returns a distinct, greppable reason string
    ("no CPV match", "no region match (found: ...)", "value X below min Y",
    "excluded by keyword '...'", "excluded by role-hint keyword '...'",
    "no value found", "non-EUR currency (...)"). Right now that reason is
    only surfaced via the per-match print in run(); it is NOT currently
    tallied anywhere. To diagnose which filter is actually starving a
    company for matches, collect these reasons into a Counter (see the
    REASON_COUNTS hook below) instead of just printing the accepted ones --
    the rejection reasons are more informative than the matches when a
    company's count is stuck near zero.
    """

    text_blob = get_release_text_blob(release)

    for kw in profile.get("exclude_keywords", []):
        if kw.lower() in text_blob:
            return False, f"excluded by keyword '{kw}'"

    for kw in profile.get("role_hint_reject", []):
        if kw.lower() in text_blob:
            return False, f"excluded by role-hint keyword '{kw}'"

    cpvs = get_release_cpvs(release)
    cpv_prefixes = profile["cpv_prefixes"]
    if not any(cpv.startswith(p) for cpv in cpvs for p in cpv_prefixes):
        return False, "no CPV match"

    regions = get_release_regions(release)
    nuts_prefixes = profile["nuts_prefixes"]
    if not any(r.startswith(p) for r in regions for p in nuts_prefixes):
        return False, f"no region match (found: {regions or 'none'})"

    amount, currency = get_release_value(release)
    if amount is None:
        return False, "no value found"
    if currency and currency != "EUR":
        return False, f"non-EUR currency ({currency})"

    vmin = profile.get("value_min")
    vmax = profile.get("value_max")
    if vmin is not None and amount < vmin:
        return False, f"value {amount:,.0f} below min {vmin:,.0f}"
    if vmax is not None and amount > vmax:
        return False, f"value {amount:,.0f} above max {vmax:,.0f}"

    return True, "match"


def render_markdown(release, company_key, profile):
    tender = release.get("tender", {})
    buyer = release.get("buyer", {})
    amount, currency = get_release_value(release)
    cpvs = get_release_cpvs(release)
    regions = sorted(get_release_regions(release))

    title = tender.get("title", "No title")
    description = tender.get("description", "").strip()
    buyer_name = buyer.get("name", "Unknown buyer")
    notice_id = release.get("id", "unknown")
    ocid = release.get("ocid", "")
    date = release.get("date", "")
    procurement_method = tender.get("procurementMethod", "")
    documents = tender.get("documents", [])
    doc_links = "\n".join(f"- {d.get('url')}" for d in documents if d.get("url"))

    value_str = f"{amount:,.2f} {currency}" if amount is not None else "N/A"

    md = f"""# {title}

**Company fit:** {profile['display_name']}
**Buyer:** {buyer_name}
**Value:** {value_str}
**CPV codes:** {', '.join(cpvs) if cpvs else 'N/A'}
**Region(s):** {', '.join(regions) if regions else 'N/A'}
**Procurement method:** {procurement_method or 'N/A'}
**Published:** {date}
**Notice ID:** {notice_id}
**OCID:** {ocid}

## Description

{description or '_No description provided._'}

## Documents

{doc_links or '_No documents listed._'}

---
_Matched against {profile['display_name']} profile: {profile.get('notes', '')}_
"""
    return md


def load_seen_ids(company_dir: Path) -> set:
    seen_file = company_dir / ".seen_ids.txt"
    if seen_file.exists():
        return set(seen_file.read_text(encoding="utf-8").splitlines())
    return set()


def save_seen_id(company_dir: Path, notice_id: str):
    seen_file = company_dir / ".seen_ids.txt"
    with open(seen_file, "a", encoding="utf-8") as f:
        f.write(notice_id + "\n")


def run(target_count: int, max_days_back: int, company_filter=None, filters_path: Path = DEFAULT_FILTERS_PATH):
    # DIAGNOSTIC HOOK (currently informational only, not wired into control
    # flow): reject reasons per company, keyed on the leading phrase of the
    # reason string returned by matches_profile() (e.g. "no CPV match",
    # "no region match", "value ... below min ..." collapses to "value").
    # Once there's a real need to diagnose why a company's count is stuck,
    # call matches_profile() for every release (not just until a company's
    # target is hit) and tally reason.split(" (")[0].split("'")[0] here per
    # company key, then print reject_reason_counts[key].most_common() in the
    # summary block below. Left as a plain dict-of-Counters stub so wiring
    # it in later is a small, localized change rather than a rewrite.
    from collections import Counter
    reject_reason_counts = {}  # company_key -> Counter(reason_prefix -> count)

    companies = load_companies(filters_path)
    if company_filter:
        companies = {k: v for k, v in companies.items() if k in company_filter}
        missing = set(company_filter) - set(companies)
        if missing:
            print(f"Warning: unknown company keys ignored: {missing}")

    OUTPUT_ROOT.mkdir(exist_ok=True)

    # Fresh run: wipe each company's existing output folder (old .md files
    # and the .seen_ids.txt tracker) before collecting anything, so stale
    # matches from a previous filters.yaml never linger alongside new ones.
    state = {}
    for key in companies:
        company_dir = OUTPUT_ROOT / key
        if company_dir.exists():
            shutil.rmtree(company_dir)
        company_dir.mkdir(parents=True, exist_ok=True)
        state[key] = {
            "dir": company_dir,
            "seen": load_seen_ids(company_dir),  # always empty right after a wipe
            "count": 0,
        }
        reject_reason_counts[key] = Counter()
        print(f"{companies[key]['display_name']}: cleared old output, starting fresh (0/{target_count}).")

    day = datetime.now() - timedelta(days=1)
    days_walked = 0

    while days_walked < max_days_back:
        remaining = {k for k in companies if state[k]["count"] < target_count}
        if not remaining:
            print("\nAll companies have reached their target count.")
            break

        pub_day = day.strftime("%Y-%m-%d")
        print(f"\n=== Day {days_walked + 1}: {pub_day} "
              f"(still need: {', '.join(remaining)}) ===")

        try:
            releases = list(fetch_day_releases(pub_day))
        except StopIteration:
            break

        for release, _fname in releases:
            notice_id = release.get("id", "")
            for key in remaining:
                profile = companies[key]
                st = state[key]
                if notice_id in st["seen"]:
                    continue
                ok, reason = matches_profile(release, profile)
                if not ok:
                    # Cheap tally for later diagnosis -- see the
                    # DIAGNOSTIC HOOK comment above run(). Not printed by
                    # default; inspect reject_reason_counts[key] yourself
                    # (e.g. in a debugger or by adding a print in the
                    # summary block) when match volume looks off.
                    reject_reason_counts[key][reason.split(" (")[0].split("'")[0]] += 1
                if ok:
                    md = render_markdown(release, key, profile)
                    out_path = st["dir"] / f"{notice_id}.md"
                    out_path.write_text(md, encoding="utf-8")
                    st["seen"].add(notice_id)
                    save_seen_id(st["dir"], notice_id)
                    st["count"] += 1
                    print(f"  [{key}] MATCH ({st['count']}/{target_count}): "
                          f"{release.get('tender', {}).get('title', '')[:70]}")
                    if st["count"] >= target_count:
                        break  # this company is done; still check others below in outer loop

        day -= timedelta(days=1)
        days_walked += 1

    print("\n=== Summary ===")
    for key, st in state.items():
        print(f"{companies[key]['display_name']}: {st['count']}/{target_count} "
              f"-> {st['dir']}")
        if st["count"] < target_count:
            print(f"  (Did not reach target within {days_walked} days walked back. "
                  f"Consider loosening filters in company_profiles.py or raising --max-days.)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET_COUNT,
                         help="Number of matching tenders to collect per company.")
    parser.add_argument("--max-days", type=int, default=DEFAULT_MAX_DAYS_BACK,
                         help="Safety cap on how many days to walk backward.")
    parser.add_argument("--companies", nargs="*", default=None,
                         help="Restrict to specific company keys (default: all).")
    parser.add_argument("--filters", type=Path, default=DEFAULT_FILTERS_PATH,
                         help=f"Path to the YAML filter file (default: {DEFAULT_FILTERS_PATH}).")
    args = parser.parse_args()

    run(args.target, args.max_days, args.companies, args.filters)


if __name__ == "__main__":
    main()