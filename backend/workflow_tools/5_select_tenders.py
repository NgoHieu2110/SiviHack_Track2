"""
backend/workflow_tools/5_select_tenders.py

Reads backend/tenders/<company_key>/index.json (maintained by
3_run_filter_for_tenders.py -- see tender_index.py for the priority rules)
and picks `count` tenders with the highest priority for that company.

There is no more "standardized" schema -- backend/standardized_tenders/ and
4_standardize_tenders.py are gone. Each result here is the raw matched
tender markdown as fetch_tenders_oeffentlichevergabe.py wrote it
(full embedded OCDS JSON and all), plus its notice_id and the handful of
cached display fields (title/authority/value/currency/deadline) that live
in index.json:

    {
      "id": "<notice_id>",
      "title": ..., "authority": ..., "value": ..., "currency": ...,
      "deadline": ..., "priority": <priority at selection time>,
      "markdown": "<full contents of tenders/<company_key>/<notice_id>.md>",
    }

Selecting a tender resets its priority back to 0 in index.json (see
tender_index.mark_selected), so a repeat call won't just keep handing back
the same tender(s) every time.

Importable use:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "select_tenders", "5_select_tenders.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tenders = mod.select_tenders(company_key="acme_gmbh", count=3)

(The leading digit means this file can't be imported with a plain
`import 5_select_tenders` statement -- see 1_company_md_to_company_details.py's
docstring for why, and the same importlib pattern applies here.)

Usage:
    python 5_select_tenders.py --company acme_gmbh
    python 5_select_tenders.py --company acme_gmbh --count 3
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DEFAULT_TENDERS_DIR = BACKEND_DIR / "tenders"
DEFAULT_COUNT = 3


def load_tender_index_module():
    path = SCRIPT_DIR / "tender_index.py"
    if not path.exists():
        raise FileNotFoundError(f"tender_index.py not found at {path} (expected next to this script)")
    spec = importlib.util.spec_from_file_location("tender_index", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tender_index = load_tender_index_module()


def select_tenders(
    company_key: str,
    count: int = DEFAULT_COUNT,
    tenders_dir: Path = DEFAULT_TENDERS_DIR,
) -> list:
    """Library entry point: pick up to `count` of company_key's
    highest-priority tenders from index.json and return each as a dict
    with its id, cached metadata, and full raw markdown (see module
    docstring). Resets the priority of whatever it picks.

    Raises FileNotFoundError / ValueError (never sys.exit) so it's safe to
    call from other code, e.g. a web backend.
    """
    tenders_dir = Path(tenders_dir)
    company_dir = tenders_dir / company_key
    if not company_dir.exists():
        raise FileNotFoundError(f"no tenders folder for '{company_key}' at {company_dir}")

    index_data = tender_index.load_index(company_dir)
    if not index_data["tenders"]:
        raise ValueError(
            f"index.json for {company_dir} has no tenders -- has "
            f"3_run_filter_for_tenders.py been run for this company yet?"
        )

    top_ids = tender_index.pick_top(company_dir, count)

    results = []
    for notice_id in top_ids:
        md_path = company_dir / f"{notice_id}.md"
        if not md_path.exists():
            print(f"  SKIP {notice_id}: indexed but .md file missing on disk")
            continue
        entry = index_data["tenders"].get(notice_id, {})
        results.append({
            "id": notice_id,
            "title": entry.get("title"),
            "authority": entry.get("authority"),
            "value": entry.get("value"),
            "currency": entry.get("currency"),
            "deadline": entry.get("deadline"),
            "priority": entry.get("priority"),
            "markdown": md_path.read_text(encoding="utf-8"),
        })

    if not results:
        raise ValueError(f"none of the top-priority ids for {company_dir} had a matching .md file on disk")

    tender_index.mark_selected(company_dir, [r["id"] for r in results])
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--company", required=True, help="Company key (folder name under tenders/)")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help=f"How many to pick (default: {DEFAULT_COUNT})")
    parser.add_argument("--tenders-dir", type=Path, default=DEFAULT_TENDERS_DIR)
    args = parser.parse_args()

    try:
        tenders = select_tenders(
            company_key=args.company,
            count=args.count,
            tenders_dir=args.tenders_dir,
        )
    except (FileNotFoundError, ValueError) as e:
        sys.exit(f"ERROR: {e}")

    print(json.dumps(tenders, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()