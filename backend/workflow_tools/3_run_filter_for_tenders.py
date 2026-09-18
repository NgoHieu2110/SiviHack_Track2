"""
backend/workflow_tools/3_run_filter_for_tenders.py

Runs fetch_tenders_oeffentlichevergabe.py (backend/oeffentlichevergabe/) with
a given filters.yaml, producing the set of markdown files for tenders that
match the filters -- written to backend/tenders/ regardless of where
fetch_tenders_oeffentlichevergabe.py itself lives.

After the fetch runs and before index.json is touched, this script also
checks backend/tenders_seen/ and deletes any freshly-fetched .md file whose
ocid is already sitting there -- i.e. a tender the user already
dismissed via 6_user_select_remove_tenders.py. This is a safety net on top
of fetch_tenders_oeffentlichevergabe.py's own .seen_ids.txt (which is
append-only and should already prevent this on its own); see
drop_already_seen_tenders() below for when it actually matters.

After that, this script updates backend/tenders/index.json (via
tender_index.sync_index_with_folder, see tender_index.py for the full
rules): every tender still present on disk gets its priority bumped,
newly-found tenders are added at priority 1, and tenders whose .md file no
longer exists are dropped from the index. This is the only place
index.json gets written from a fetch run; 5_select_tenders.py only reads
it (and resets priority on the ones it picks).

Importable use:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_filter_for_tenders", "3_run_filter_for_tenders.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    mod.run_filter_for_tenders(target=40, max_days=90)

(The leading digit means this file can't be imported with a plain `import
3_run_filter_for_tenders` statement -- see 1_company_md_to_company_details.py's
docstring for why, and the same importlib pattern applies here.)

Expected layout (paths default accordingly, all overridable via flags):
    backend/
      oeffentlichevergabe/
        fetch_tenders_oeffentlichevergabe.py
      workflow_tools/
        3_run_filter_for_tenders.py   <- this script
        filters.yaml                   <- from 2_company_details_to_initial_filter.py
      tenders/                         <- output lands here, one flat folder

Usage:
    python 3_run_filter_for_tenders.py
    python 3_run_filter_for_tenders.py --target 40 --max-days 90
    python 3_run_filter_for_tenders.py --filters other_filters.yaml
"""

import argparse
import importlib.util
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

DEFAULT_FETCH_MODULE_PATH = BACKEND_DIR / "oeffentlichevergabe" / "fetch_tenders_oeffentlichevergabe.py"
DEFAULT_FILTERS_PATH = SCRIPT_DIR / "filters.yaml"
DEFAULT_OUTPUT_DIR = BACKEND_DIR / "tenders"
DEFAULT_TENDERS_SEEN_DIR = BACKEND_DIR / "tenders_seen"

DEFAULT_TARGET_COUNT = 15
DEFAULT_MAX_DAYS_BACK = 90


def load_fetch_module(module_path: Path):
    """Import fetch_tenders_oeffentlichevergabe.py by path (it isn't on
    sys.path and its filename can't be imported as a normal module name from
    a numbered sibling script), so this loads it directly from disk."""
    if not module_path.exists():
        raise FileNotFoundError(
            f"fetch module not found at {module_path}\n"
            f"Pass fetch_module_path to point at fetch_tenders_oeffentlichevergabe.py explicitly."
        )
    spec = importlib.util.spec_from_file_location("fetch_tenders_oeffentlichevergabe", module_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise RuntimeError(f"failed to import {module_path}: {e}") from e

    for attr in ("run", "load_filters", "OUTPUT_ROOT"):
        if not hasattr(module, attr):
            raise RuntimeError(
                f"{module_path} is missing expected attribute '{attr}' -- "
                f"is this the right file?"
            )
    return module


def load_tender_index_module():
    """Import tender_index.py by path, same reasoning as load_fetch_module:
    kept explicit/by-path rather than relying on sys.path so this script
    works regardless of cwd."""
    path = SCRIPT_DIR / "tender_index.py"
    if not path.exists():
        raise FileNotFoundError(f"tender_index.py not found at {path} (expected next to this script)")
    spec = importlib.util.spec_from_file_location("tender_index", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def drop_already_seen_tenders(output_dir: Path, tenders_seen_dir: Path) -> None:
    """Safety net against re-adding a tender the user already dismissed.

    fetch_tenders_oeffentlichevergabe.py's own .seen_ids.txt is supposed to
    make this impossible on its own -- it's append-only and never cleared,
    even once 6_user_select_remove_tenders.py moves a tender's .md out to
    tenders_seen/ (see that script's docstring). This exists only in case
    that guard is ever out of sync -- .seen_ids.txt deleted by hand, a file
    dropped into tenders_seen/ some other way, or tender_index.mark_removed()
    having failed for a given id (6_...py logs a warning but doesn't fail
    the removal when that happens).

    Called after the fetch has already run and written this run's new .md
    files, but before sync_index_with_folder() -- so anything deleted here
    never makes it into index.json at all.
    """
    output_dir = Path(output_dir)
    tenders_seen_dir = Path(tenders_seen_dir)
    if not output_dir.exists() or not tenders_seen_dir.exists():
        return

    already_seen_ids = {p.stem for p in tenders_seen_dir.glob("*.md")}
    for md_path in output_dir.glob("*.md"):
        if md_path.stem in already_seen_ids:
            print(f"  dropping freshly-fetched {md_path.name} "
                  f"-- already sitting in {tenders_seen_dir} (previously removed by the user)")
            md_path.unlink()


def run_filter_for_tenders(
    filters_path: Path = DEFAULT_FILTERS_PATH,
    fetch_module_path: Path = DEFAULT_FETCH_MODULE_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    tenders_seen_dir: Path = DEFAULT_TENDERS_SEEN_DIR,
    target: int = DEFAULT_TARGET_COUNT,
    max_days: int = DEFAULT_MAX_DAYS_BACK,
    log_dir: Path = None,
):
    """Library entry point mirroring the CLI: run
    fetch_tenders_oeffentlichevergabe.py's own run() against filters.yaml,
    drop anything that duplicates a previously-dismissed tender, then sync
    index.json. Raises FileNotFoundError / RuntimeError / ValueError on
    failure instead of calling sys.exit.

    All path arguments accept str or Path.
    """
    filters_path = Path(filters_path)
    fetch_module_path = Path(fetch_module_path)
    output_dir = Path(output_dir)
    tenders_seen_dir = Path(tenders_seen_dir)

    print(f"Fetch module:      {fetch_module_path}")
    print(f"Filters:           {filters_path}")
    print(f"Output dir:        {output_dir}")
    print(f"Tenders seen dir:  {tenders_seen_dir}")
    print()

    module = load_fetch_module(fetch_module_path)

    if not filters_path.exists():
        raise FileNotFoundError(f"filters file not found: {filters_path}")

    # load_filters() enforces required fields (display_name, cpv_prefixes,
    # nuts_prefixes), so a structurally broken filters.yaml fails here
    # before we even attempt the fetch.
    module.load_filters(filters_path)

    # fetch_tenders_oeffentlichevergabe.py hardcodes its OUTPUT_ROOT relative
    # to its own script location; override it here so results land in
    # backend/tenders regardless of where the fetch module itself lives.
    output_dir.mkdir(parents=True, exist_ok=True)
    module.OUTPUT_ROOT = output_dir

    result = module.run(target, max_days, filters_path, log_dir=log_dir)

    print("\nChecking for tenders already dismissed (present in tenders_seen/)...")
    drop_already_seen_tenders(output_dir, tenders_seen_dir)

    # Bump/seed priority in index.json for this run.
    tender_index = load_tender_index_module()
    print("\nUpdating index.json...")
    index_data = tender_index.sync_index_with_folder(output_dir)
    print(f"  {len(index_data['tenders'])} tender(s) tracked in index.json")

    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--filters", type=Path, default=DEFAULT_FILTERS_PATH,
                         help=f"Path to filters.yaml (default: {DEFAULT_FILTERS_PATH})")
    parser.add_argument("--fetch-module", type=Path, default=DEFAULT_FETCH_MODULE_PATH,
                         help=f"Path to fetch_tenders_oeffentlichevergabe.py (default: {DEFAULT_FETCH_MODULE_PATH})")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                         help=f"Where matched tender markdown files are written (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--tenders-seen-dir", type=Path, default=DEFAULT_TENDERS_SEEN_DIR,
                         help=f"Where 6_user_select_remove_tenders.py moves dismissed tenders "
                              f"(checked so they don't get re-added; default: {DEFAULT_TENDERS_SEEN_DIR})")
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET_COUNT,
                         help=f"Number of matching tenders to collect (default: {DEFAULT_TARGET_COUNT})")
    parser.add_argument("--max-days", type=int, default=DEFAULT_MAX_DAYS_BACK,
                         help=f"Safety cap on how many days to walk backward (default: {DEFAULT_MAX_DAYS_BACK})")
    parser.add_argument("--log-dir", type=Path, default=None,
                         help="Where to write debug/summary log files "
                              "(default: backend/logs, next to backend/tenders)")
    args = parser.parse_args()

    try:
        run_filter_for_tenders(
            filters_path=args.filters,
            fetch_module_path=args.fetch_module,
            output_dir=args.output_dir,
            tenders_seen_dir=args.tenders_seen_dir,
            target=args.target,
            max_days=args.max_days,
            log_dir=args.log_dir,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        sys.exit(f"ERROR: {e}")


if __name__ == "__main__":
    main()