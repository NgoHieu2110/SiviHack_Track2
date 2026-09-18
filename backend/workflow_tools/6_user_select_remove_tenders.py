"""
backend/workflow_tools/6_user_select_remove_tenders.py

Called when the user dismisses/removes a tender from the frontend (a
notice_id they were shown and don't want to see again). This:

  1. Moves backend/tenders/<company_key>/<notice_id>.md to
     backend/tenders_seen/<company_key>/<notice_id>.md -- SAME nested
     per-company layout as tenders/, not flat. A flat tenders_seen/ was
     considered and rejected: the same notice_id can legitimately match
     more than one company's filters, so a flat layout would let removing
     it for one company delete the file out from under another.
  2. Marks that tender "removed" in backend/tenders/<company_key>/index.json
     via tender_index.mark_removed() -- the index ROW is kept (not
     deleted) as a seen/rejected history, with its priority floored to
     tender_index.REMOVED_PRIORITY and pick_top() permanently skipping it,
     even though its .md file has physically moved out of tenders/.

Both index.json and the raw tender store live under backend/tenders/ --
see tender_index.py. .seen_ids.txt (fetch_tenders_oeffentlichevergabe.py's
own dedup tracker) is untouched by this script on purpose: it exists to
stop the SAME notice being re-fetched/re-written into tenders/ by a future
run, which should still hold true for a removed tender.

Importable use:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "user_select_remove_tenders", "6_user_select_remove_tenders.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    mod.remove_tender(company_key="acme_gmbh", notice_id="ocds-213-...-1")

(The leading digit means this file can't be imported with a plain
`import 6_user_select_remove_tenders` statement -- see
1_company_md_to_company_details.py's docstring for why, and the same
importlib pattern applies here.)

Usage:
    python 6_user_select_remove_tenders.py --company acme_gmbh --notice-id ocds-213-...-1
"""

import argparse
import importlib.util
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DEFAULT_TENDERS_DIR = BACKEND_DIR / "tenders"
DEFAULT_TENDERS_SEEN_DIR = BACKEND_DIR / "tenders_seen"


def load_tender_index_module():
    path = SCRIPT_DIR / "tender_index.py"
    if not path.exists():
        raise FileNotFoundError(f"tender_index.py not found at {path} (expected next to this script)")
    spec = importlib.util.spec_from_file_location("tender_index", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tender_index = load_tender_index_module()


def remove_tender(
    company_key: str,
    notice_id: str,
    tenders_dir: Path = DEFAULT_TENDERS_DIR,
    tenders_seen_dir: Path = DEFAULT_TENDERS_SEEN_DIR,
) -> dict:
    """Move tenders/<company_key>/<notice_id>.md to
    tenders_seen/<company_key>/<notice_id>.md and mark it removed in
    tenders/<company_key>/index.json.

    Idempotent: calling this again on an already-removed notice_id returns
    {"status": "already_removed", ...} instead of raising, since "the user
    dismissed something already dismissed" isn't really a failure.

    Raises FileNotFoundError if the tender was never there at all for this
    company (wrong id, wrong company_key, or it was never selected/fetched
    for them in the first place) -- never sys.exit, safe to call from other
    code / a web backend.
    """
    tenders_dir = Path(tenders_dir)
    tenders_seen_dir = Path(tenders_seen_dir)

    company_dir = tenders_dir / company_key
    src_path = company_dir / f"{notice_id}.md"

    if not src_path.exists():
        index_data = tender_index.load_index(company_dir) if company_dir.exists() else {"tenders": {}}
        entry = index_data["tenders"].get(notice_id)
        if entry and entry.get("removed"):
            return {
                "status": "already_removed",
                "companyKey": company_key,
                "id": notice_id,
                "removedAt": entry.get("removed_at"),
            }
        raise FileNotFoundError(
            f"no tender '{notice_id}' found at {src_path} for company '{company_key}'"
        )

    dest_dir = tenders_seen_dir / company_key
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{notice_id}.md"

    shutil.move(str(src_path), str(dest_path))
    print(f"  moved {src_path} -> {dest_path}")

    try:
        tender_index.mark_removed(company_dir, notice_id)
    except KeyError as e:
        # File existed but was never indexed (shouldn't normally happen --
        # 3_run_filter_for_tenders.py indexes everything it writes). Don't
        # leave the .md file stranded in limbo: the move already happened,
        # so surface this as a warning, not a failed removal.
        print(f"  WARNING: {e} (file was still moved to tenders_seen/)")

    return {"status": "removed", "companyKey": company_key, "id": notice_id, "movedTo": str(dest_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--company", required=True, help="Company key (folder name under tenders/)")
    parser.add_argument("--notice-id", required=True, help="notice_id of the tender to remove (the .md filename, minus extension)")
    parser.add_argument("--tenders-dir", type=Path, default=DEFAULT_TENDERS_DIR)
    parser.add_argument("--tenders-seen-dir", type=Path, default=DEFAULT_TENDERS_SEEN_DIR)
    args = parser.parse_args()

    try:
        result = remove_tender(
            company_key=args.company,
            notice_id=args.notice_id,
            tenders_dir=args.tenders_dir,
            tenders_seen_dir=args.tenders_seen_dir,
        )
    except FileNotFoundError as e:
        sys.exit(f"ERROR: {e}")

    print(result)


if __name__ == "__main__":
    main()