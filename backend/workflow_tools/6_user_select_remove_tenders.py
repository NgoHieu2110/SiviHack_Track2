"""
backend/workflow_tools/6_user_select_remove_tenders.py

Called when the user dismisses/removes a tender from the frontend. The
frontend sends back the tender's full raw markdown (the same "markdown"
string 5_select_tenders.py handed it -- see that script's docstring), not
a notice_id, so this script extracts the notice_id itself: it's release
["id"] from the "## Full raw release JSON" block embedded in that
markdown, the exact same field fetch_tenders_oeffentlichevergabe.py used
as the .md filename in the first place. Once it has that id, this:

  1. Moves backend/tenders/<notice_id>.md to
     backend/tenders_seen/<notice_id>.md -- both flat, one folder each
     (there's only ever one company/profile per backend instance, so
     there's no cross-company id-collision risk to guard a nested layout
     against).
  2. Marks that tender "removed" in backend/tenders/index.json via
     tender_index.mark_removed() -- the index ROW is kept (not deleted) as
     a seen/rejected history, with its priority floored to
     tender_index.REMOVED_PRIORITY and pick_top() permanently skipping it,
     even though its .md file has physically moved out of tenders/.

Both index.json and the raw tender store live under backend/tenders/ --
see tender_index.py. .seen_ids.txt (fetch_tenders_oeffentlichevergabe.py's
own dedup tracker) is untouched by this script on purpose: it exists to
stop the SAME notice being re-fetched/re-written into tenders/ by a future
run, which should still hold true for a removed tender.

NOTE on trusting the frontend's copy: the notice_id is extracted from
whatever markdown the frontend sends, not re-read from disk first. The
lookup that follows (tenders/<notice_id>.md) still only ever touches the
real file on disk -- the frontend-supplied markdown is used solely to
recover the id, never written anywhere itself. If the extracted id doesn't
correspond to a real file, this fails the same way a bad notice_id would
(see remove_tender()'s FileNotFoundError).

Importable use:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "user_select_remove_tenders", "6_user_select_remove_tenders.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    mod.remove_tender(markdown=full_md_text)

(The leading digit means this file can't be imported with a plain
`import 6_user_select_remove_tenders` statement -- see
1_company_md_to_company_details.py's docstring for why, and the same
importlib pattern applies here.)

Usage:
    python 6_user_select_remove_tenders.py --md-file ./tender.md
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


def notice_id_from_markdown(markdown: str) -> str:
    """Pulls release["id"] out of the "## Full raw release JSON" block
    embedded in a tender's raw markdown -- the same block/field
    tender_index.py's own extract_release_json()/sync_index_with_folder()
    read. Raises ValueError if the block is missing/unparseable, or if the
    release JSON has no "id"."""
    release = tender_index.extract_release_json(markdown)
    notice_id = release.get("id")
    if not notice_id:
        raise ValueError("release JSON in the given markdown has no 'id' field")
    return notice_id


def remove_tender(
    markdown: str,
    tenders_dir: Path = DEFAULT_TENDERS_DIR,
    tenders_seen_dir: Path = DEFAULT_TENDERS_SEEN_DIR,
) -> dict:
    """Extracts the notice_id from `markdown` (see notice_id_from_markdown),
    then moves tenders/<notice_id>.md to tenders_seen/<notice_id>.md and
    marks it removed in tenders/index.json.

    Idempotent: calling this again for an already-removed tender returns
    {"status": "already_removed", ...} instead of raising, since "the user
    dismissed something already dismissed" isn't really a failure.

    Raises ValueError if `markdown` doesn't contain a valid embedded
    release (can't recover a notice_id from it at all). Raises
    FileNotFoundError if the (successfully extracted) notice_id was never
    on disk. Never sys.exit -- safe to call from other code / a web
    backend.
    """
    notice_id = notice_id_from_markdown(markdown)

    tenders_dir = Path(tenders_dir)
    tenders_seen_dir = Path(tenders_seen_dir)

    src_path = tenders_dir / f"{notice_id}.md"

    if not src_path.exists():
        index_data = tender_index.load_index(tenders_dir) if tenders_dir.exists() else {"tenders": {}}
        entry = index_data["tenders"].get(notice_id)
        if entry and entry.get("removed"):
            return {
                "status": "already_removed",
                "id": notice_id,
                "removedAt": entry.get("removed_at"),
            }
        raise FileNotFoundError(f"no tender '{notice_id}' found at {src_path}")

    tenders_seen_dir.mkdir(parents=True, exist_ok=True)
    dest_path = tenders_seen_dir / f"{notice_id}.md"

    shutil.move(str(src_path), str(dest_path))
    print(f"  moved {src_path} -> {dest_path}")

    try:
        tender_index.mark_removed(tenders_dir, notice_id)
    except KeyError as e:
        # File existed but was never indexed (shouldn't normally happen --
        # 3_run_filter_for_tenders.py indexes everything it writes). Don't
        # leave the .md file stranded in limbo: the move already happened,
        # so surface this as a warning, not a failed removal.
        print(f"  WARNING: {e} (file was still moved to tenders_seen/)")

    return {"status": "removed", "id": notice_id, "movedTo": str(dest_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--md-file", required=True, type=Path,
                         help="Path to a local copy of the tender's raw markdown (used only to extract its notice_id)")
    parser.add_argument("--tenders-dir", type=Path, default=DEFAULT_TENDERS_DIR)
    parser.add_argument("--tenders-seen-dir", type=Path, default=DEFAULT_TENDERS_SEEN_DIR)
    args = parser.parse_args()

    if not args.md_file.exists():
        sys.exit(f"ERROR: --md-file not found: {args.md_file}")
    markdown = args.md_file.read_text(encoding="utf-8")

    try:
        result = remove_tender(
            markdown=markdown,
            tenders_dir=args.tenders_dir,
            tenders_seen_dir=args.tenders_seen_dir,
        )
    except (FileNotFoundError, ValueError) as e:
        sys.exit(f"ERROR: {e}")

    print(result)


if __name__ == "__main__":
    main()