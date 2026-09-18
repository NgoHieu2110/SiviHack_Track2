"""
backend/workflow_tools/4_standardize_tenders.py

Standardizes the raw per-tender markdown files fetch_tenders_oeffentlichevergabe.py
writes into backend/tenders/<company_key>/<notice_id>.md, so they resemble
example-tender.md: a YAML frontmatter block with a fixed set of normalized
fields, followed by a plain-text description body. Output is written to
backend/standardized_tenders/<company_key>/<notice_id>.md (mirroring the
input's per-company folder structure).

Importable use:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "standardize_tenders", "4_standardize_tenders.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    mod.standardize_tenders(companies=["brenner_sohn_tiefbau"])

(The leading digit means this file can't be imported with a plain `import
4_standardize_tenders` statement -- see 1_company_md_to_company_details.py's
docstring for why, and the same importlib pattern applies here.)

HOW THIS WORKS
---------------
The raw markdown fetch_tenders_oeffentlichevergabe.py writes always embeds
the full, original OCDS release JSON verbatim under a "## Full raw release
JSON" section (see its render_markdown()). This script extracts that JSON
block and maps fields from it directly -- no LLM call, fully deterministic,
nothing invented.

FIELD MAPPING (target schema, from example-tender.md)
--------------------------------------------------------
Reliably derivable from the OCDS release JSON:
    id            <- release.id
    title         <- tender.title
    authority     <- buyer.name
    cpvCode       <- tender.items[0].classification.id (fallback: first
                     additionalClassifications entry)
    cpvLabel      <- "{cpvCode} - {classification.description}" if a
                     description is present, else just cpvCode
    contractNature <- tender.mainProcurementCategory, title-cased
                     (goods/works/services -> Goods/Works/Services)
    location      <- item deliveryAddress (locality, region, country),
                     falling back to buyer.address
    value         <- tender.value.amount, falling back to summed lot values
    currency      <- tender.value.currency (or lot currency fallback)
    deadline      <- tender.tenderPeriod.endDate, as YYYY-MM-DD
    startDate     <- earliest tender.lots[].contractPeriod.startDate (or
                     tender.contractPeriod.startDate), as YYYY-MM-DD
    (body text)   <- tender.description, falling back to joined lot
                     titles/descriptions, falling back to
                     procurementMethodRationale

NOT reliably present in this data source (German OCDS notices don't carry
a standard equivalent), so populated as null/[] rather than guessed:
    role                (no field distinguishes sole-contractor vs. JV)
    requiredCertificates (no standard qualification/certificate list field)
    insuranceRequired    (no standard field)
    guaranteeRequired    (no standard field)
These four are left as explicit null/[] so it's obvious at a glance which
fields are real data vs. unmapped, rather than silently blank or fabricated.
If real data patterns emerge (e.g. from inspect_release.py samples showing
these ARE populated on some notices), extend the extractor functions below.

Usage:
    python 4_standardize_tenders.py
    python 4_standardize_tenders.py --companies brenner_sohn_tiefbau
    python 4_standardize_tenders.py --input-dir ../tenders --output-dir ../standardized_tenders
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DEFAULT_INPUT_DIR = BACKEND_DIR / "tenders"
DEFAULT_OUTPUT_DIR = BACKEND_DIR / "standardized_tenders"

JSON_BLOCK_RE = re.compile(
    r"## Full raw release JSON\s*```json\s*(.*?)```", re.DOTALL
)


# ---- extraction helpers (mirror fetch_tenders_oeffentlichevergabe.py's own
# ---- logic where a direct equivalent exists, so results stay consistent
# ---- with what that script itself used to decide the tender matched) ------

def extract_release_json(md_text: str) -> dict:
    match = JSON_BLOCK_RE.search(md_text)
    if not match:
        raise ValueError("no '## Full raw release JSON' fenced block found")
    return json.loads(match.group(1))


def get_value(release: dict):
    tender = release.get("tender", {})
    val = tender.get("value", {}) or {}
    amount = val.get("amount")
    currency = val.get("currency")
    if amount is not None:
        return amount, currency

    total, found, lot_currency = 0.0, False, None
    for lot in tender.get("lots", []) or []:
        lv = (lot.get("value") or {})
        if lv.get("amount") is not None:
            total += lv["amount"]
            lot_currency = lv.get("currency", lot_currency)
            found = True
    return (total, lot_currency) if found else (None, None)


def get_primary_cpv(release: dict):
    tender = release.get("tender", {})
    for item in tender.get("items", []) or []:
        cls = item.get("classification") or {}
        if cls.get("id"):
            return cls.get("id"), cls.get("description")
    for cls in tender.get("additionalClassifications", []) or []:
        if cls.get("id"):
            return cls.get("id"), cls.get("description")
    for item in tender.get("items", []) or []:
        for cls in item.get("additionalClassifications", []) or []:
            if cls.get("id"):
                return cls.get("id"), cls.get("description")
    return None, None


def get_contract_nature(release: dict):
    category = release.get("tender", {}).get("mainProcurementCategory")
    if isinstance(category, str) and category:
        return category.strip().title()
    return None


def get_location(release: dict):
    tender = release.get("tender", {})
    for item in tender.get("items", []) or []:
        addr = item.get("deliveryAddress") or {}
        parts = [addr.get("locality"), addr.get("region"), addr.get("countryName") or addr.get("country")]
        parts = [p for p in parts if p]
        if parts:
            return ", ".join(parts)

    buyer_addr = release.get("buyer", {}).get("address", {}) or {}
    parts = [buyer_addr.get("locality"), buyer_addr.get("region"), buyer_addr.get("countryName") or buyer_addr.get("country")]
    parts = [p for p in parts if p]
    return ", ".join(parts) if parts else None


def _date_only(iso_str):
    if not iso_str or not isinstance(iso_str, str):
        return None
    return iso_str.split("T")[0]


def get_deadline(release: dict):
    return _date_only(release.get("tender", {}).get("tenderPeriod", {}).get("endDate"))


def get_start_date(release: dict):
    tender = release.get("tender", {})
    starts = []
    for lot in tender.get("lots", []) or []:
        d = (lot.get("contractPeriod") or {}).get("startDate")
        if d:
            starts.append(d)
    if starts:
        return _date_only(min(starts))
    return _date_only((tender.get("contractPeriod") or {}).get("startDate"))


def get_description(release: dict):
    tender = release.get("tender", {})
    desc = tender.get("description")
    if desc:
        return desc.strip()

    parts = []
    for lot in tender.get("lots", []) or []:
        if lot.get("title"):
            parts.append(lot["title"])
        if lot.get("description"):
            parts.append(lot["description"])
    if parts:
        return "\n\n".join(parts).strip()

    rationale = tender.get("procurementMethodRationale")
    return rationale.strip() if rationale else ""


def build_standardized_record(release: dict) -> dict:
    amount, currency = get_value(release)
    cpv_code, cpv_desc = get_primary_cpv(release)
    cpv_label = f"{cpv_code} \u2014 {cpv_desc}" if (cpv_code and cpv_desc) else cpv_code

    return {
        "id": release.get("id"),
        "title": release.get("tender", {}).get("title"),
        "authority": release.get("buyer", {}).get("name"),
        "cpvCode": cpv_code,
        "cpvLabel": cpv_label,
        "contractNature": get_contract_nature(release),
        "location": get_location(release),
        "value": amount,
        "currency": currency,
        "deadline": get_deadline(release),
        # Not reliably present in this data source -- see module docstring.
        "role": None,
        "requiredCertificates": [],
        "insuranceRequired": None,
        "guaranteeRequired": None,
        "startDate": get_start_date(release),
        "_body": get_description(release),
    }


# ---- rendering --------------------------------------------------------

def yaml_scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return f"{value:g}" if isinstance(value, float) else str(value)
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_frontmatter(record: dict) -> str:
    lines = ["---"]
    for key in ("id", "title", "authority", "cpvCode", "cpvLabel", "contractNature",
                "location", "value", "currency", "deadline", "role"):
        lines.append(f"{key}: {yaml_scalar(record[key])}")

    certs = record["requiredCertificates"]
    if certs:
        lines.append("requiredCertificates:")
        for c in certs:
            lines.append(f"  - {yaml_scalar(c)}")
    else:
        lines.append("requiredCertificates: []")

    for key in ("insuranceRequired", "guaranteeRequired", "startDate"):
        lines.append(f"{key}: {yaml_scalar(record[key])}")
    lines.append("---")
    return "\n".join(lines)


def render_standardized_markdown(record: dict) -> str:
    body = record["_body"] or ""
    return render_frontmatter(record) + "\n" + body.strip() + "\n"


# ---- driver -------------------------------------------------------------

def process_company_folder(company_dir: Path, out_dir: Path) -> tuple:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ok, skipped = 0, 0
    for md_path in sorted(company_dir.glob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
            release = extract_release_json(text)
            record = build_standardized_record(release)
            standardized = render_standardized_markdown(record)
        except Exception as e:
            print(f"    SKIP {md_path.name}: {e}")
            skipped += 1
            continue

        (out_dir / md_path.name).write_text(standardized, encoding="utf-8")
        ok += 1

    return ok, skipped


def standardize_tenders(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    companies: list = None,
) -> dict:
    """Library entry point mirroring the CLI: standardize every per-company
    folder of raw tender markdown under input_dir into output_dir. Returns
    a summary dict {"total_ok": int, "total_skipped": int, "companies":
    {company_name: {"ok": int, "skipped": int, "output_dir": str}}}.

    Raises FileNotFoundError / ValueError instead of calling sys.exit, so
    it's safe to call from other code.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"input dir not found: {input_dir}")

    company_dirs = [d for d in sorted(input_dir.iterdir()) if d.is_dir()]
    if companies:
        company_dirs = [d for d in company_dirs if d.name in companies]
        if not company_dirs:
            raise ValueError(f"no matching company folders under {input_dir} for {companies}")

    if not company_dirs:
        raise ValueError(f"no company folders found under {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Input dir:  {input_dir}")
    print(f"Output dir: {output_dir}\n")

    total_ok, total_skipped = 0, 0
    per_company = {}
    for company_dir in company_dirs:
        out_dir = output_dir / company_dir.name
        print(f"{company_dir.name}:")
        ok, skipped = process_company_folder(company_dir, out_dir)
        total_ok += ok
        total_skipped += skipped
        per_company[company_dir.name] = {"ok": ok, "skipped": skipped, "output_dir": str(out_dir)}
        print(f"  {ok} standardized, {skipped} skipped -> {out_dir}")

    print(f"\nDone. {total_ok} standardized, {total_skipped} skipped across {len(company_dirs)} companies.")

    return {"total_ok": total_ok, "total_skipped": total_skipped, "companies": per_company}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR,
                         help=f"Folder containing per-company raw tender markdown (default: {DEFAULT_INPUT_DIR})")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                         help=f"Where standardized markdown is written (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--companies", nargs="*", default=None,
                         help="Restrict to specific company-folder names (default: all)")
    args = parser.parse_args()

    try:
        standardize_tenders(input_dir=args.input_dir, output_dir=args.output_dir, companies=args.companies)
    except (FileNotFoundError, ValueError) as e:
        sys.exit(f"ERROR: {e}")


if __name__ == "__main__":
    main()