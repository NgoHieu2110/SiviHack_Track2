"""
backend/workflow_tools/7_select_from_raw_tenders.py

Reads RAW (non-standardized) tender .md files that
3_run_filter_for_tenders.py writes directly to backend/tenders/*.md. Each
file has a human-readable **Field:** header, some dev-facing debug
sections, and a fenced ```json block containing the full raw OCDS release.

Structured Tender fields (id, title, authority, cpvCode, cpvLabel,
contractNature, location, value, currency, deadline, startDate) are
extracted deterministically from that raw JSON block -- not guessed by an
LLM, so they stay exact. Every OTHER piece of information in the .md
(buyer contact, documents, procurement method, notice/OCID, matched-filter
notes) is appended at the very bottom of the returned tender's
`description`. The full original .md text is also kept as `markdown`, so
/tenders/remove (6_user_select_remove_tenders.py, which extracts the
notice_id from that raw markdown) keeps working against tenders selected
this way.

GEMINI is used only for what it's good at: comparing the parsed tenders
against a company profile, picking the best `count` of them, and
explaining why (score + reasons + considerations + summary).

Single-company backend: unlike the earlier 6_select_from_raw_tenders.py,
there is no per-company subfolder here -- .md files sit directly in
TENDERS_DIR (backend/tenders/*.md), matching this backend's single flat
company_details.json.

Importable use:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "select_from_raw", "7_select_from_raw_tenders.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    matches = mod.select_tenders_with_ai_from_raw(profile=profile_dict, count=3)

(The leading digit means this file can't be imported with a plain
`import 7_select_from_raw_tenders` statement -- see
1_company_md_to_company_details.py's docstring for why, and the same
importlib pattern applies here.)

Usage:
    python 7_select_from_raw_tenders.py --count 3
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from common import get_gemini_api_key

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DEFAULT_RAW_TENDERS_DIR = BACKEND_DIR / "tenders"
DEFAULT_COMPANY_DETAILS_PATH = SCRIPT_DIR / "company_details.json"
DEFAULT_COUNT = 3

# NOTE: same model-retirement caveat as elsewhere in this project -- if this
# stops resolving, check https://ai.google.dev/gemini-api/docs/models for
# the current name and set GEMINI_MODEL in your .env (no code change needed).
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

RAW_JSON_BLOCK_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)
BOLD_FIELD_RE = re.compile(r"^\*\*([^:*]+):\*\*\s*(.+)$", re.MULTILINE)
NOTES_LINE_RE = re.compile(r"^_(Matched against.*)_\s*$", re.MULTILINE)

_CATEGORY_TO_CONTRACT_NATURE = {
    "works": "Works",
    "services": "Services",
    "goods": "Supplies",
    "supplies": "Supplies",
}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_raw_tender_md(path: Path) -> dict:
    """Parse one RAW tender .md into a Tender-shaped dict.

    Core fields come straight from the embedded raw OCDS JSON (exact, not
    LLM-guessed). `description` is the tender/lot description plus every
    other piece of information from the .md's readable header, appended
    below a divider at the bottom. `markdown` carries the full original
    file text through unchanged, for callers (like /tenders/remove) that
    need to re-derive the notice_id from it.
    """
    text = path.read_text(encoding="utf-8")

    json_match = RAW_JSON_BLOCK_RE.search(text)
    if not json_match:
        raise ValueError(f"{path.name}: no fenced ```json raw release block found")
    try:
        release = json.loads(json_match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"{path.name}: raw release JSON block is invalid: {e}") from e

    tender = release.get("tender") or {}
    buyer = release.get("buyer") or {}
    items = tender.get("items") or []
    lots = tender.get("lots") or []
    value = tender.get("value") or {}

    first_item = items[0] if items else {}
    classification = first_item.get("classification") or {}
    first_lot = lots[0] if lots else {}
    delivery_address = first_item.get("deliveryAddress") or {}
    buyer_address = buyer.get("address") or {}

    contract_nature = _CATEGORY_TO_CONTRACT_NATURE.get(
        (tender.get("mainProcurementCategory") or "").lower(), ""
    )

    location = ", ".join(
        p for p in [
            delivery_address.get("locality") or buyer_address.get("locality"),
            delivery_address.get("region") or buyer_address.get("region"),
            delivery_address.get("countryName") or buyer_address.get("countryName"),
        ] if p
    )

    core_description = tender.get("description") or ""
    lot_description = first_lot.get("description") or ""
    if lot_description and lot_description not in core_description:
        core_description = (core_description + "\n\n" + lot_description).strip()

    # --- everything else in the file, appended at the bottom -----------
    header_fields = dict(BOLD_FIELD_RE.findall(text))
    notes_match = NOTES_LINE_RE.search(text)
    notes = notes_match.group(1).strip() if notes_match else ""
    contact = buyer.get("contactPoint") or {}
    doc_links = [d.get("url") for d in (tender.get("documents") or []) if d.get("url")]

    extra_lines = []
    for label in [
        "Matched company", "Buyer", "Value (as matched)", "CPV codes (as matched)",
        "Region(s) (as matched)", "Published", "Notice ID", "OCID",
    ]:
        if label in header_fields:
            extra_lines.append(f"- **{label}:** {header_fields[label]}")
    contact_bits = " ".join(
        filter(None, [contact.get("name"), contact.get("email"), contact.get("telephone")])
    )
    if contact_bits:
        extra_lines.append(f"- **Buyer contact:** {contact_bits}")
    if tender.get("procurementMethodDetails"):
        extra_lines.append(f"- **Procurement method:** {tender['procurementMethodDetails']}")
    if doc_links:
        extra_lines.append(f"- **Documents:** {', '.join(doc_links)}")

    full_description = core_description
    if extra_lines or notes:
        full_description += "\n\n---\n\n## Additional details\n" + "\n".join(extra_lines)
        if notes:
            full_description += f"\n\n_{notes}_"

    return {
        "id": release.get("id") or tender.get("id") or path.stem,
        "title": tender.get("title") or header_fields.get("Buyer", path.stem),
        "authority": buyer.get("name", ""),
        "cpvCode": classification.get("id", ""),
        "cpvLabel": classification.get("description", ""),
        "contractNature": contract_nature,
        "location": location,
        "value": value.get("amount") or 0,
        "currency": value.get("currency") or "EUR",
        "deadline": (tender.get("tenderPeriod") or {}).get("endDate", ""),
        "role": "",
        "requiredCertificates": [],
        "insuranceRequired": 0,
        "guaranteeRequired": "",
        "startDate": "",
        "description": full_description.strip(),
        "markdown": text,  # full raw .md content, for /tenders/remove
    }


def _load_all_raw_tenders(raw_dir: Path) -> list:
    """Read every raw .md directly under raw_dir (flat -- no per-company
    subfolder). Files that fail to parse are skipped (noted via print())
    rather than aborting. Raises FileNotFoundError / ValueError, never
    sys.exit, so it's safe to call from other code (e.g. a web backend)."""
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        raise FileNotFoundError(f"no tenders folder at {raw_dir}")

    md_files = sorted(raw_dir.glob("*.md"))
    if not md_files:
        raise ValueError(f"no raw tender files found in {raw_dir}")

    tenders = []
    for path in md_files:
        try:
            tenders.append(parse_raw_tender_md(path))
        except Exception as e:
            print(f"  SKIP {path.name}: {e}")

    if not tenders:
        raise ValueError(f"found {len(md_files)} file(s) in {raw_dir} but none parsed successfully")

    return tenders


# ---------------------------------------------------------------------------
# AI-based selection + explanation
# ---------------------------------------------------------------------------

def _build_selection_prompt(profile: dict, tenders: list[dict], count: int) -> str:
    tender_blocks = []
    for t in tenders:
        tender_blocks.append(
            f"""---
id: {t.get("id")}
title: {t.get("title")}
authority: {t.get("authority")}
cpvCode: {t.get("cpvCode")} ({t.get("cpvLabel")})
contractNature: {t.get("contractNature")}
location: {t.get("location")}
value: {t.get("value")} {t.get("currency")}
deadline: {t.get("deadline")}
role: {t.get("role")}
requiredCertificates: {", ".join(t.get("requiredCertificates") or []) or "none"}
insuranceRequired: {t.get("insuranceRequired")} {t.get("currency")}
guaranteeRequired: {t.get("guaranteeRequired")}
startDate: {t.get("startDate")}
description: {t.get("description")}
---"""
        )

    return f"""You are a procurement analyst. Compare a company's profile
against a list of tender packages and pick the {count} BEST matches,
scoring and explaining each one.

COMPANY PROFILE:
- does (company's line of work / scope of activity): {profile.get("does")}
- placeOfPerformance (where the company can operate): {profile.get("placeOfPerformance")}
- target contract value range: {profile.get("contractValueMin")} to {profile.get("contractValueMax")}
- specifications (technical capabilities/equipment/methods): {profile.get("specifications") or "none stated"}
- exclusions (things the company cannot/will not do): {profile.get("exclusions") or "none"}
- annual revenue: {profile.get("revenue")}
- number of employees: {profile.get("employees")}

TENDERS ({len(tenders)} total, already pre-filtered by CPV/region/value):
{chr(10).join(tender_blocks)}

Evaluate fit considering:
1. Scope match: does the company's line of work ("does") align with the
   tender's cpvCode/cpvLabel/description, including whether the tender's
   own contractNature (Works/Services/Supplies) is something this kind of
   company would realistically bid on
2. Location match (placeOfPerformance vs tender location)
3. Whether the tender value falls within the company's target value range
4. Technical fit: do the company's specifications match what the tender
   description/requirements call for
5. Financial/operational capacity: is the company's revenue and employee
   count plausible for a contract of this value, insurance requirement,
   and guarantee requirement (flag as a consideration if it looks like a
   stretch; note required certificates as an open item to verify rather
   than assuming the company has or lacks them)
6. Any exclusions that would disqualify the company from this tender

Select the {count} tenders that are the BEST fit overall (fewer if there
are genuinely not {count} reasonable options). Return ONLY a JSON array
(no markdown fences, no commentary), ordered best-fit first, in this
exact shape:

[
  {{
    "id": "<tender id, copied exactly>",
    "score": <integer 0-100, overall fit>,
    "reasons": ["short bullet reasons this is a good fit", "..."],
    "considerations": ["short bullet caveats/risks/gaps to watch for", "..."],
    "summary": "one or two sentence plain-language summary of the fit"
  }}
]

Only include tenders you are actually selecting -- do not return all
{len(tenders)}, only the top {count} (or fewer, if fewer are genuinely a
reasonable fit)."""


def _extract_json_array(text: str) -> list:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


def select_tenders_with_ai_from_raw(
    profile: dict,
    count: int = DEFAULT_COUNT,
    raw_dir: Path = DEFAULT_RAW_TENDERS_DIR,
) -> list:
    """Read every raw .md in raw_dir, ask Gemini to pick the `count` best
    matches against `profile`, and return TenderMatch-shaped dicts
    (tender + score + reasons + considerations + summary) ready to hand
    straight to the frontend.

    Raises FileNotFoundError / ValueError / RuntimeError, never sys.exit,
    so it's safe to call from other code (e.g. a web backend).
    """
    tenders = _load_all_raw_tenders(raw_dir)

    if len(tenders) <= count:
        print(
            f"  Only {len(tenders)} tender(s) available (<= requested {count}) -- "
            f"asking Gemini to rank/explain all of them."
        )

    from google import genai
    from google.genai import types

    api_key = get_gemini_api_key()
    client = genai.Client(api_key=api_key)

    prompt = _build_selection_prompt(profile, tenders, count)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
    except Exception as e:  # noqa: BLE001 -- surface any Gemini error uniformly
        raise RuntimeError(f"Gemini call failed while selecting tenders: {e}") from e

    if not response.text:
        raise RuntimeError("Gemini returned an empty response while selecting tenders.")

    try:
        raw_results = _extract_json_array(response.text)
    except (json.JSONDecodeError, TypeError) as e:
        raise RuntimeError(f"Could not parse Gemini's response as JSON: {e}") from e

    tenders_by_id = {t.get("id"): t for t in tenders if t.get("id")}
    matches = []
    for item in raw_results:
        tender = tenders_by_id.get(item.get("id"))
        if tender is None:
            # Gemini referenced an id we don't recognize -- skip it rather
            # than fail the whole selection.
            continue
        matches.append(
            {
                "tender": tender,
                "score": max(0, min(100, int(item.get("score", 0)))),
                "reasons": item.get("reasons", []),
                "considerations": item.get("considerations", []),
                "summary": item.get("summary", ""),
            }
        )

    if not matches:
        raise ValueError("Gemini did not select any recognizable tenders from the candidates.")

    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches[:count]


def _load_profile(company_details_path: Path) -> dict:
    """CLI-only convenience: this backend keeps a single flat company
    profile in company_details.json (not a {"companies": [...]} list)."""
    if not company_details_path.exists():
        raise FileNotFoundError(f"company details file not found: {company_details_path}")
    return json.loads(company_details_path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help=f"How many to pick (default: {DEFAULT_COUNT})")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_TENDERS_DIR)
    parser.add_argument("--company-details", type=Path, default=DEFAULT_COMPANY_DETAILS_PATH, help="Path to company_details.json")
    args = parser.parse_args()

    try:
        profile = _load_profile(args.company_details)
        result = select_tenders_with_ai_from_raw(
            profile=profile,
            count=args.count,
            raw_dir=args.raw_dir,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        sys.exit(f"ERROR: {e}")

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()