"""
backend/workflow_tools/3_run_filter_for_tenders.py

Runs fetch_tenders_oeffentlichevergabe.py (backend/oeffentlichevergabe/) with
a given filters.yaml, producing a set of per-company markdown files with the
tenders that match the filters -- written to backend/tenders/<company_key>/
regardless of where fetch_tenders_oeffentlichevergabe.py itself lives.

Before running, this script sanity-checks filters.yaml against
company_details.json: every company key in filters.yaml must correspond to
a company actually listed in company_details.json (matched via the same
slugify() fetch_tenders_oeffentlichevergabe.py itself uses), so a stale or
hand-edited filters.yaml can't silently run against a company that no
longer exists in company_details.json. This is a validation-only use of
company_details.json -- the fetch/filter logic itself is driven entirely by
filters.yaml, exactly as before.

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
        company_details.json           <- from 1_company_md_to_company_details.py
      tenders/                         <- output lands here, one folder per company

Usage:
    python 3_run_filter_for_tenders.py
    python 3_run_filter_for_tenders.py --target 40 --max-days 90
    python 3_run_filter_for_tenders.py --companies brenner_sohn_tiefbau_gmbh
    python 3_run_filter_for_tenders.py --filters other_filters.yaml --force
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

DEFAULT_FETCH_MODULE_PATH = BACKEND_DIR / "oeffentlichevergabe" / "fetch_tenders_oeffentlichevergabe.py"
DEFAULT_FILTERS_PATH = SCRIPT_DIR / "filters.yaml"
DEFAULT_COMPANY_DETAILS_PATH = SCRIPT_DIR / "company_details.json"
DEFAULT_OUTPUT_DIR = BACKEND_DIR / "tenders"

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

    for attr in ("run", "load_companies", "slugify", "OUTPUT_ROOT"):
        if not hasattr(module, attr):
            raise RuntimeError(
                f"{module_path} is missing expected attribute '{attr}' -- "
                f"is this the right file?"
            )
    return module


def validate_filters_against_company_details(filters_companies: dict, company_details_path: Path, slugify) -> list:
    """Every key in filters_companies (from filters.yaml) must correspond to
    a company actually present in company_details.json. Returns a list of
    hard-error strings (empty list = all good). Also prints soft warnings
    for display_name mismatches, which don't block the run."""
    if not company_details_path.exists():
        return [f"company_details.json not found at {company_details_path}"]

    with open(company_details_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            return [f"could not parse {company_details_path} as JSON: {e}"]

    known_companies = data.get("companies", [])
    if not known_companies:
        return [f"{company_details_path} has no companies listed"]

    slug_to_name = {slugify(c.get("name", "")): c.get("name", "") for c in known_companies}

    errors = []
    for key, profile in filters_companies.items():
        if key not in slug_to_name:
            errors.append(
                f"filters.yaml company '{key}' has no matching entry in "
                f"{company_details_path.name} (known: {sorted(slug_to_name)})"
            )
            continue
        display_name = profile.get("display_name", "")
        real_name = slug_to_name[key]
        if display_name and display_name != real_name:
            print(
                f"  WARNING: '{key}' display_name ({display_name!r}) does not exactly "
                f"match company_details.json name ({real_name!r}) -- not blocking, "
                f"just worth checking for drift."
            )
    return errors


def run_filter_for_tenders(
    filters_path: Path = DEFAULT_FILTERS_PATH,
    company_details_path: Path = DEFAULT_COMPANY_DETAILS_PATH,
    fetch_module_path: Path = DEFAULT_FETCH_MODULE_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    target: int = DEFAULT_TARGET_COUNT,
    max_days: int = DEFAULT_MAX_DAYS_BACK,
    companies: list = None,
    force: bool = False,
):
    """Library entry point mirroring the CLI: validate filters.yaml against
    company_details.json, then run fetch_tenders_oeffentlichevergabe.py's
    own run() against that filters.yaml. Raises FileNotFoundError /
    RuntimeError / ValueError on failure instead of calling sys.exit.

    All path arguments accept str or Path.
    """
    filters_path = Path(filters_path)
    company_details_path = Path(company_details_path)
    fetch_module_path = Path(fetch_module_path)
    output_dir = Path(output_dir)

    print(f"Fetch module:      {fetch_module_path}")
    print(f"Filters:           {filters_path}")
    print(f"Company details:   {company_details_path}")
    print(f"Output dir:        {output_dir}")
    print()

    module = load_fetch_module(fetch_module_path)

    if not filters_path.exists():
        raise FileNotFoundError(f"filters file not found: {filters_path}")

    # load_companies() also enforces required fields (display_name,
    # cpv_prefixes, nuts_prefixes), so a structurally broken filters.yaml
    # fails here before we even get to the company_details.json check.
    filters_companies = module.load_companies(filters_path)

    print("Validating filters.yaml against company_details.json...")
    errors = validate_filters_against_company_details(filters_companies, company_details_path, module.slugify)
    if errors:
        print("\nVALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        if force:
            print("\nforce=True given: continuing despite the above.\n")
        else:
            raise ValueError(
                "Aborting before running the fetch. Fix filters.yaml / "
                "company_details.json, or pass force=True to run anyway. "
                "Errors: " + "; ".join(errors)
            )
    else:
        print("  OK: every company in filters.yaml matches an entry in company_details.json.\n")

    # fetch_tenders_oeffentlichevergabe.py hardcodes its OUTPUT_ROOT relative
    # to its own script location; override it here so results land in
    # backend/tenders regardless of where the fetch module itself lives.
    output_dir.mkdir(parents=True, exist_ok=True)
    module.OUTPUT_ROOT = output_dir

    return module.run(target, max_days, companies, filters_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--filters", type=Path, default=DEFAULT_FILTERS_PATH,
                         help=f"Path to filters.yaml (default: {DEFAULT_FILTERS_PATH})")
    parser.add_argument("--company-details", type=Path, default=DEFAULT_COMPANY_DETAILS_PATH,
                         help=f"Path to company_details.json, used for validation only (default: {DEFAULT_COMPANY_DETAILS_PATH})")
    parser.add_argument("--fetch-module", type=Path, default=DEFAULT_FETCH_MODULE_PATH,
                         help=f"Path to fetch_tenders_oeffentlichevergabe.py (default: {DEFAULT_FETCH_MODULE_PATH})")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                         help=f"Where matched tender markdown files are written (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET_COUNT,
                         help=f"Number of matching tenders to collect per company (default: {DEFAULT_TARGET_COUNT})")
    parser.add_argument("--max-days", type=int, default=DEFAULT_MAX_DAYS_BACK,
                         help=f"Safety cap on how many days to walk backward (default: {DEFAULT_MAX_DAYS_BACK})")
    parser.add_argument("--companies", nargs="*", default=None,
                         help="Restrict to specific company keys from filters.yaml (default: all)")
    parser.add_argument("--force", action="store_true",
                         help="Run even if the company_details.json validation finds mismatches")
    args = parser.parse_args()

    try:
        run_filter_for_tenders(
            filters_path=args.filters,
            company_details_path=args.company_details,
            fetch_module_path=args.fetch_module,
            output_dir=args.output_dir,
            target=args.target,
            max_days=args.max_days,
            companies=args.companies,
            force=args.force,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        sys.exit(f"ERROR: {e}")


if __name__ == "__main__":
    main()