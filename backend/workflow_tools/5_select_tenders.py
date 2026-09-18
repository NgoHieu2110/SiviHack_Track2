"""
backend/workflow_tools/5_select_tenders.py

Reads backend/tenders/index.json (maintained by 3_run_filter_for_tenders.py
-- see tender_index.py for the priority rules) and picks `count` tenders
with the highest priority.

There is no more "standardized" schema -- backend/standardized_tenders/ and
4_standardize_tenders.py are gone. Each result here is the raw matched
tender markdown as fetch_tenders_oeffentlichevergabe.py wrote it
(full embedded OCDS JSON and all), plus its ocid and the handful of
cached display fields (title/authority/value/currency/deadline) that live
in index.json:

    {
      "id": "<ocid>",
      "title": ..., "authority": ..., "value": ..., "currency": ...,
      "deadline": ..., "priority": <priority at selection time>,
      "markdown": "<full contents of tenders/<ocid>.md>",
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

    tenders = mod.select_tenders(count=3)

(The leading digit means this file can't be imported with a plain
`import 5_select_tenders` statement -- see 1_company_md_to_company_details.py's
docstring for why, and the same importlib pattern applies here.)

Usage:
    python 5_select_tenders.py
    python 5_select_tenders.py --count 3
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
    count: int = DEFAULT_COUNT,
    tenders_dir: Path = DEFAULT_TENDERS_DIR,
) -> list:
    """Library entry point: pick up to `count` highest-priority tenders
    from index.json and return each as a dict with its id, cached
    metadata, and full raw markdown (see module docstring). Resets the
    priority of whatever it picks.

    Raises FileNotFoundError / ValueError (never sys.exit) so it's safe to
    call from other code, e.g. a web backend.
    """
    tenders_dir = Path(tenders_dir)
    if not tenders_dir.exists():
        raise FileNotFoundError(f"no tenders folder at {tenders_dir}")

    index_data = tender_index.load_index(tenders_dir)
    if not index_data["tenders"]:
        raise ValueError(
            f"index.json for {tenders_dir} has no tenders -- has "
            f"3_run_filter_for_tenders.py been run yet?"
        )

    top_ids = tender_index.pick_top(tenders_dir, count)

    results = []
    for ocid in top_ids:
        md_path = tenders_dir / f"{ocid}.md"
        if not md_path.exists():
            print(f"  SKIP {ocid}: indexed but .md file missing on disk")
            continue
        entry = index_data["tenders"].get(ocid, {})
        results.append({
            "id": ocid,
            "title": entry.get("title"),
            "authority": entry.get("authority"),
            "value": entry.get("value"),
            "currency": entry.get("currency"),
            "deadline": entry.get("deadline"),
            "priority": entry.get("priority"),
            "markdown": md_path.read_text(encoding="utf-8"),
        })

    if not results:
        raise ValueError(f"none of the top-priority ids for {tenders_dir} had a matching .md file on disk")

    tender_index.mark_selected(tenders_dir, [r["id"] for r in results])
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help=f"How many to pick (default: {DEFAULT_COUNT})")
    parser.add_argument("--tenders-dir", type=Path, default=DEFAULT_TENDERS_DIR)
    args = parser.parse_args()

    try:
        tenders = select_tenders(
            count=args.count,
            tenders_dir=args.tenders_dir,
        )
    except (FileNotFoundError, ValueError) as e:
        sys.exit(f"ERROR: {e}")

    print(json.dumps(tenders, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()