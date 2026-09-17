"""
Fetch German public tenders from oeffentlichevergabe.de and sort them into
per-company markdown files based on hard filters (CPV prefix, NUTS region,
value range, exclusion keywords).

For each company in company_profiles.COMPANIES, this walks backward day by
day from yesterday until it has collected TARGET_COUNT matching tenders (or
hits MAX_DAYS_BACK), writing one markdown file per matching tender into:

    oeffentlichevergabe/<company_slug>/<notice_id>.md

Usage:
    python fetch_tenders.py
    python fetch_tenders.py --target 40 --max-days 90
    python fetch_tenders.py --companies brenner_sohn_tiefbau

Re-running is safe: a per-company "seen ids" file prevents duplicate
downloads.md and skips ahead automatically as more days accumulate.
"""
import argparse
import io
import json
import re
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import requests

from company_profiles import COMPANIES

API_URL = "https://oeffentlichevergabe.de/api/notice-exports"
OUTPUT_ROOT = Path("oeffentlichevergabe")

DEFAULT_TARGET_COUNT = 40
DEFAULT_MAX_DAYS_BACK = 180  # safety cap so a bad filter config can't loop forever


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
    minus exclusion/role-hint keywords. Returns (bool, reason_str)."""

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


def run(target_count: int, max_days_back: int, company_filter=None):
    companies = COMPANIES
    if company_filter:
        companies = {k: v for k, v in COMPANIES.items() if k in company_filter}
        missing = set(company_filter) - set(companies)
        if missing:
            print(f"Warning: unknown company keys ignored: {missing}")

    OUTPUT_ROOT.mkdir(exist_ok=True)

    # Track progress per company independently.
    state = {}
    for key in companies:
        company_dir = OUTPUT_ROOT / key
        company_dir.mkdir(parents=True, exist_ok=True)
        state[key] = {
            "dir": company_dir,
            "seen": load_seen_ids(company_dir),
            "count": len(list(company_dir.glob("*.md"))),
        }
        print(f"{companies[key]['display_name']}: {state[key]['count']}/{target_count} already on disk.")

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
    args = parser.parse_args()

    run(args.target, args.max_days, args.companies)


if __name__ == "__main__":
    main()