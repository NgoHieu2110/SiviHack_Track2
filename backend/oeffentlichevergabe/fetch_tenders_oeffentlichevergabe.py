"""
backend/oeffentlichevergabe/fetch_tenders_oeffentlichevergabe.py

Fetch German public tenders from oeffentlichevergabe.de and sort them into
markdown files based on hard filters (CPV prefix, NUTS region, value range,
exclusion keywords).

Filters are NOT hardcoded in this file. They live in filters.yaml (next to
this script), which you edit directly (plain YAML, no Python) to fine-tune
matching. filters.yaml is now a single flat block of filter fields -- there
is only ever one company/profile per backend instance, so there's no
company-key wrapper around it.

This walks backward day by day from yesterday until it has collected
TARGET_COUNT *new* matching tenders (or hits MAX_DAYS_BACK), writing one
markdown file per matching tender into:

    tenders/<notice_id>.md

Each run is INCREMENTAL, not a fresh wipe: the existing .md files and the
.seen_ids.txt tracker (tenders/.seen_ids.txt) are kept, so previously
matched tenders stay on disk and TARGET_COUNT new ones are added on top
each time this runs. This is what lets 3_run_filter_for_tenders.py's
index.json track a rising "priority" per tender across repeated runs.
Re-running after loosening a filter will therefore accumulate matches over
time rather than resetting; if a genuinely clean slate is needed, delete
tenders/ yourself before running.

Usage:
    python fetch_tenders_oeffentlichevergabe.py
    python fetch_tenders_oeffentlichevergabe.py --target 40 --max-days 90
    python fetch_tenders_oeffentlichevergabe.py --filters my_filters.yaml

filters.yaml is resolved relative to this script's own location, so it works
regardless of which directory you run the command from.
"""
import argparse
import io
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

API_URL = "https://oeffentlichevergabe.de/api/notice-exports"
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = SCRIPT_DIR / "tenders"
DEFAULT_FILTERS_PATH = SCRIPT_DIR / "filters.yaml"

DEFAULT_TARGET_COUNT = 7
DEFAULT_MAX_DAYS_BACK = 60  # safety cap so a bad filter config can't loop forever

REQUIRED_FIELDS = ["display_name", "cpv_prefixes", "nuts_prefixes"]

# Optional filter fields wired into matches_profile(), with their defaults.
# All are "lenient by default": leaving them unset/null in filters.yaml means
# they have zero effect on matching (same behavior as before they existed).
# See filters.yaml's header and filters.json for the full field reference.
OPTIONAL_FIELD_DEFAULTS = {
    "value_min": None,
    "value_max": None,
    "exclude_keywords": [],
    "role_hint_reject": [],
    "procurement_methods_allowed": None,
    "min_bid_prep_days": None,
    "reject_reserved_participation": False,
    "contract_starts_after": None,
    "contract_starts_before": None,
    "notes": "",
}


def load_filters(filters_path: Path) -> dict:
    """Load and lightly validate the single flat filter profile from
    filters.yaml (a plain mapping of filter fields, not wrapped in a
    company-key block)."""
    if not filters_path.exists():
        sys.exit(f"Filter file not found: {filters_path}\n"
                  f"Expected a YAML file with the filter fields (see filters.yaml).")

    with open(filters_path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            sys.exit(f"Could not parse {filters_path} as YAML: {e}")

    if not isinstance(data, dict) or not data:
        sys.exit(f"{filters_path} must contain a mapping of filter fields "
                  f"(see filters.yaml).")

    missing = [f for f in REQUIRED_FIELDS if f not in data or data[f] in (None, [])]
    if missing:
        sys.exit(f"{filters_path} is missing required field(s): {', '.join(missing)}")

    for field, default in OPTIONAL_FIELD_DEFAULTS.items():
        data.setdefault(field, default)

    return data


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
    """Primary CPV codes (tender.items[].classification.id) PLUS secondary/
    additional classification codes, wherever they appear:
      - tender.additionalClassifications[].id (tender-level)
      - tender.items[].additionalClassifications[].id (item-level)
    Not filtered by scheme=="CPV" - same style as the original primary-code
    read below, which never checked scheme either. In practice this data
    source only populates CPV-scheme classifications here; if that changes,
    tighten this to scheme=="CPV" only."""
    tender = release.get("tender", {})
    cpvs = [
        item.get("classification", {}).get("id", "")
        for item in tender.get("items", [])
        if item.get("classification", {}).get("id")
    ]
    for cls in tender.get("additionalClassifications", []) or []:
        cid = cls.get("id")
        if cid:
            cpvs.append(cid)
    for item in tender.get("items", []):
        for cls in item.get("additionalClassifications", []) or []:
            cid = cls.get("id")
            if cid:
                cpvs.append(cid)
    return cpvs


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


def _parse_ocds_date(s):
    """Parse an OCDS/ISO-8601 date(time) string, or a plain 'YYYY-MM-DD'
    filters.yaml boundary value. Returns a naive UTC datetime (any timezone
    offset is normalized away and stripped), or None if s is falsy/
    unparseable. Normalizing to naive UTC lets a plain 'YYYY-MM-DD' filter
    boundary compare safely against offset-aware OCDS timestamps like
    '2027-01-01T00:00:00+01:00' without a naive/aware TypeError."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def get_release_procurement_method(release):
    """tender.procurementMethod, lowercased. None if absent."""
    method = release.get("tender", {}).get("procurementMethod")
    return method.lower() if isinstance(method, str) and method else None


def get_release_bid_prep_days(release):
    """Days between tender.tenderPeriod.startDate and .endDate. None if the
    period (or either date) is missing/unparseable."""
    period = release.get("tender", {}).get("tenderPeriod", {}) or {}
    start = _parse_ocds_date(period.get("startDate"))
    end = _parse_ocds_date(period.get("endDate"))
    if start is None or end is None:
        return None
    return (end - start).total_seconds() / 86400.0


def get_release_reserved_participation(release):
    """tender.otherRequirements.reservedParticipation, or None if absent.
    Returned as-is (string/list/dict depending on how the source populates
    it) - callers just check truthiness."""
    other = release.get("tender", {}).get("otherRequirements", {}) or {}
    rp = other.get("reservedParticipation")
    return rp if rp else None


def get_lot_contract_start_dates(release):
    """List of parsed datetimes from each tender.lots[].contractPeriod.
    startDate that's present and parseable. Empty list if no lot has one."""
    starts = []
    for lot in release.get("tender", {}).get("lots", []) or []:
        d = _parse_ocds_date((lot.get("contractPeriod") or {}).get("startDate"))
        if d is not None:
            starts.append(d)
    return starts


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
    """Hard filter: CPV prefix AND region prefix AND value in range AND
    (optional) procurement method / bid-prep window / reserved-participation
    / lot contract-start window, minus exclusion/role-hint keywords. Returns
    (bool, reason_str).

    The five optional checks (procurement_methods_allowed, min_bid_prep_days,
    reject_reserved_participation, contract_starts_after/_before) are
    LENIENT ON MISSING DATA: if the profile sets one of them but the
    corresponding OCDS field isn't present on this particular release, that
    check is skipped (does not reject) rather than treated as a fail. This
    matches the reality that these fields are sparsely populated across
    notices (see sample_release.md) - a hard-reject-on-missing policy here
    would silently zero out matches on any day where the field happens to be
    absent. This is a different policy than value_min/value_max, which
    predate this change and hard-reject on missing value on purpose.

    DIAGNOSTIC NOTE (see filters.yaml header for the full write-up):
    every rejection path below returns a distinct, greppable reason string
    ("no CPV match", "no region match (found: ...)", "value X below min Y",
    "excluded by keyword '...'", "excluded by role-hint keyword '...'",
    "no value found", "non-EUR currency (...)", "procurement method ...",
    "bid prep window ...", "reserved participation present ...", "no lot
    contractPeriod.startDate within ..."). Right now that reason is only
    surfaced via the per-match print in run(); it is NOT currently tallied
    anywhere. To diagnose which filter is actually starving matches,
    collect these reasons into a Counter (see the DIAGNOSTIC HOOK in run())
    instead of just printing the accepted ones -- the rejection reasons are
    more informative than the matches when the match count is stuck near
    zero.
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

    allowed_methods = profile.get("procurement_methods_allowed")
    if allowed_methods:
        method = get_release_procurement_method(release)
        allowed_lower = {m.lower() for m in allowed_methods}
        if method is not None and method not in allowed_lower:
            return False, f"procurement method '{method}' not in allowed list {sorted(allowed_lower)}"
        # method is None (field absent on this release) -> lenient, don't reject

    min_days = profile.get("min_bid_prep_days")
    if min_days is not None:
        days = get_release_bid_prep_days(release)
        if days is not None and days < min_days:
            return False, f"bid prep window {days:.1f} days below min {min_days}"
        # days is None (tenderPeriod absent/unparseable) -> lenient, don't reject

    if profile.get("reject_reserved_participation"):
        rp = get_release_reserved_participation(release)
        if rp:
            return False, f"reserved participation present ({summarize_value(rp)})"

    starts_after = profile.get("contract_starts_after")
    starts_before = profile.get("contract_starts_before")
    if starts_after or starts_before:
        lot_starts = get_lot_contract_start_dates(release)
        if lot_starts:
            after_dt = _parse_ocds_date(starts_after) if starts_after else None
            before_dt = _parse_ocds_date(starts_before) if starts_before else None

            def in_range(d):
                if after_dt and d < after_dt:
                    return False
                if before_dt and d > before_dt:
                    return False
                return True

            if not any(in_range(d) for d in lot_starts):
                return False, (f"no lot contractPeriod.startDate within "
                                f"[{starts_after or '-inf'}, {starts_before or '+inf'}]")
        # lot_starts empty (no lot has contractPeriod.startDate) -> lenient, don't reject

    return True, "match"


def get_path(obj, dot_path):
    """Walk a dot path like 'tender.otherRequirements.reservedParticipation'.
    Returns (found: bool, value) - found=False if any hop is missing.
    (Same helper as inspect_release.py, duplicated here so this file has no
    import dependency on that diagnostic script.)"""
    cur = obj
    for part in dot_path.split("."):
        if isinstance(cur, list):
            if not cur:
                return False, None
            cur = cur[0]
        if not isinstance(cur, dict) or part not in cur:
            return False, None
        cur = cur[part]
    return True, cur


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


# Same field list as inspect_release.py's FIELDS_OF_INTEREST, kept here too
# so a matched-tender's .md shows the same "what's actually populated"
# inventory as the diagnostic tool, without importing that script.
FIELDS_OF_INTEREST = [
    ("tender.lots", "Per-lot breakdown (value/CPV/region can differ from tender-level)"),
    ("tender.lotDetails", "Lot-bidding constraints (maximumLotsBidPerSupplier etc.)"),
    ("tender.additionalClassifications", "Secondary CPV/classification codes beyond the primary one"),
    ("tender.otherRequirements", "reservedParticipation, requiresStaffNamesAndQualifications, securityClearance, etc."),
    ("tender.otherRequirements.reservedParticipation", "Sheltered-workshop / social-enterprise reservation codes"),
    ("tender.procurementMethod", "open / restricted / negotiated / etc."),
    ("tender.procurementMethodDetails", "Free-text procedure detail"),
    ("tender.tenderPeriod", "Submission deadline window"),
    ("tender.submissionMethodDetails", "How/where to submit a bid"),
    ("tender.value", "Tender-level estimated value"),
    ("tender.items", "Item list (CPV classification lives here today)"),
    ("parties", "All organizations involved, with roles[] per party"),
    ("buyer", "The buyer party reference"),
    ("awards", "Award-stage data (not usually present on a pre-award notice)"),
    ("contracts", "Contract-stage data (not usually present on a pre-award notice)"),
]


def render_markdown(release, profile, reason="match"):
    """Render the FULL release for a matched tender: a short "why this
    matched" summary, the field-inventory table (same as
    inspect_release.py, so you can see at a glance what else is populated
    on this specific notice), and the complete raw OCDS JSON underneath.

    This intentionally mirrors inspect_release.py's render_markdown() so
    the two tools produce the same shape of document - the only difference
    is this one is written for every real match instead of one ad-hoc
    sample, and it's prefixed with the match context (reason, values
    fetch_tenders.py actually filtered on).
    """
    tender = release.get("tender", {})
    buyer = release.get("buyer", {})
    amount, currency = get_release_value(release)
    cpvs = get_release_cpvs(release)
    regions = sorted(get_release_regions(release))

    title = tender.get("title", "No title")
    buyer_name = buyer.get("name", "Unknown buyer")
    notice_id = release.get("id", "unknown")
    ocid = release.get("ocid", "")
    date = release.get("date", "")

    value_str = f"{amount:,.2f} {currency}" if amount is not None else "N/A"

    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Matched company:** {profile['display_name']}")
    lines.append(f"**Buyer:** {buyer_name}")
    lines.append(f"**Value (as matched):** {value_str}")
    lines.append(f"**CPV codes (as matched):** {', '.join(cpvs) if cpvs else 'N/A'}")
    lines.append(f"**Region(s) (as matched):** {', '.join(regions) if regions else 'N/A'}")
    lines.append(f"**Published:** {date}")
    lines.append(f"**Notice ID:** {notice_id}")
    lines.append(f"**OCID:** {ocid}")
    lines.append("")
    lines.append(
        f"_Matched against the filters.yaml profile ({reason}). "
        f"Notes: {profile.get('notes', '')}_"
    )
    lines.append("")

    # --- Field inventory (same as inspect_release.py) -----------------------
    lines.append("## Field inventory")
    lines.append("")
    lines.append(
        "What's actually populated on this release, beyond the handful of "
        "fields fetch_tenders.py currently filters on. Useful when deciding "
        "whether a field is reliable enough to add to filters.yaml as a "
        "real filter (see filters.yaml's own header for that workflow)."
    )
    lines.append("")
    lines.append("| Field (path) | What it would let you filter on | Status on this release |")
    lines.append("|---|---|---|")
    for path, purpose in FIELDS_OF_INTEREST:
        found, val = get_path(release, path)
        status = summarize_value(val) if found else "_NOT PRESENT_"
        lines.append(f"| `{path}` | {purpose} | {status} |")
    lines.append("")

    # --- Fields currently used for matching ---------------------------------
    lines.append("## Fields fetch_tenders.py used to decide this match")
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
    lines.append("- `tender.additionalClassifications[].id`, "
                  "`tender.items[].additionalClassifications[].id` (secondary CPV "
                  "codes, folded into the same CPV match pool as the primary code)")
    lines.append("- `tender.procurementMethod` (if `procurement_methods_allowed` is set)")
    lines.append("- `tender.tenderPeriod.startDate`/`.endDate` (if `min_bid_prep_days` is set)")
    lines.append("- `tender.otherRequirements.reservedParticipation` "
                  "(if `reject_reserved_participation` is set)")
    lines.append("- `tender.lots[].contractPeriod.startDate` "
                  "(if `contract_starts_after`/`contract_starts_before` is set)")
    lines.append("")

    # --- Full raw JSON -------------------------------------------------------
    lines.append("## Full raw release JSON")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(release, indent=2, ensure_ascii=False))
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def load_seen_ids(tenders_dir: Path) -> set:
    seen_file = tenders_dir / ".seen_ids.txt"
    if seen_file.exists():
        return set(seen_file.read_text(encoding="utf-8").splitlines())
    return set()


def save_seen_id(tenders_dir: Path, notice_id: str):
    seen_file = tenders_dir / ".seen_ids.txt"
    with open(seen_file, "a", encoding="utf-8") as f:
        f.write(notice_id + "\n")


def run(target_count: int, max_days_back: int, filters_path: Path = DEFAULT_FILTERS_PATH):
    # DIAGNOSTIC HOOK (currently informational only, not wired into control
    # flow): reject reasons, keyed on the leading phrase of the reason
    # string returned by matches_profile() (e.g. "no CPV match",
    # "no region match", "value ... below min ..." collapses to "value").
    # Once there's a real need to diagnose why the match count is stuck,
    # tally reason.split(" (")[0].split("'")[0] into reject_reason_counts
    # for every release (not just until target is hit), then print
    # reject_reason_counts.most_common() in the summary block below. Left
    # as a plain Counter stub so wiring it in later is a small, localized
    # change rather than a rewrite.
    reject_reason_counts = Counter()

    profile = load_filters(filters_path)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    # Incremental run: existing .md files and .seen_ids.txt are kept (never
    # wiped), so previously matched tenders stay on disk and target_count
    # new ones are added on top each time this runs.
    seen = load_seen_ids(OUTPUT_ROOT)
    count = 0  # NEW matches found *this run*, not the folder total

    print(f"{profile['display_name']}: {len(seen)} previously matched tender(s) on disk, "
          f"collecting up to {target_count} new one(s) this run.")

    day = datetime.now() - timedelta(days=1)
    days_walked = 0

    while days_walked < max_days_back:
        if count >= target_count:
            print("\nTarget count reached.")
            break

        pub_day = day.strftime("%Y-%m-%d")
        print(f"\n=== Day {days_walked + 1}: {pub_day} "
              f"(still need: {target_count - count} more) ===")

        try:
            releases = list(fetch_day_releases(pub_day))
        except StopIteration:
            break

        for release, _fname in releases:
            if count >= target_count:
                break
            notice_id = release.get("id", "")
            if notice_id in seen:
                continue
            ok, reason = matches_profile(release, profile)
            if not ok:
                # Cheap tally for later diagnosis -- see the DIAGNOSTIC
                # HOOK comment above. Not printed by default; inspect
                # reject_reason_counts yourself (e.g. in a debugger or by
                # adding a print in the summary block) when match volume
                # looks off.
                reject_reason_counts[reason.split(" (")[0].split("'")[0]] += 1
                continue

            md = render_markdown(release, profile, reason=reason)
            out_path = OUTPUT_ROOT / f"{notice_id}.md"
            out_path.write_text(md, encoding="utf-8")
            seen.add(notice_id)
            save_seen_id(OUTPUT_ROOT, notice_id)
            count += 1
            print(f"  MATCH ({count}/{target_count}): "
                  f"{release.get('tender', {}).get('title', '')[:70]}")

        day -= timedelta(days=1)
        days_walked += 1

    print("\n=== Summary ===")
    print(f"{profile['display_name']}: {count}/{target_count} -> {OUTPUT_ROOT}")
    if count < target_count:
        print(f"  (Did not reach target within {days_walked} days walked back. "
              f"Consider loosening filters in filters.yaml or raising --max-days.)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET_COUNT,
                         help="Number of matching tenders to collect.")
    parser.add_argument("--max-days", type=int, default=DEFAULT_MAX_DAYS_BACK,
                         help="Safety cap on how many days to walk backward.")
    parser.add_argument("--filters", type=Path, default=DEFAULT_FILTERS_PATH,
                         help=f"Path to the YAML filter file (default: {DEFAULT_FILTERS_PATH}).")
    args = parser.parse_args()

    run(args.target, args.max_days, args.filters)


if __name__ == "__main__":
    main()