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
        sys.exit(
            f"ERROR: fetch module not found at {module_path}\n"
            f"Pass --fetch-module to point at fetch_tenders_oeffentlichevergabe.py explicitly."
        )
    spec = importlib.util.spec_from_file_location("fetch_tenders_oeffentlichevergabe", module_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        sys.exit(f"ERROR: failed to import {module_path}: {e}")

    for attr in ("run", "load_companies", "slugify", "OUTPUT_ROOT"):
        if not hasattr(module, attr):
            sys.exit(f"ERROR: {module_path} is missing expected attribute '{attr}' -- "
                      f"is this the right file?")
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

    print(f"Fetch module:      {args.fetch_module}")
    print(f"Filters:           {args.filters}")
    print(f"Company details:   {args.company_details}")
    print(f"Output dir:        {args.output_dir}")
    print()

    module = load_fetch_module(args.fetch_module)

    if not args.filters.exists():
        sys.exit(f"ERROR: filters file not found: {args.filters}")

    # load_companies() also enforces required fields (display_name,
    # cpv_prefixes, nuts_prefixes), so a structurally broken filters.yaml
    # fails here before we even get to the company_details.json check.
    filters_companies = module.load_companies(args.filters)

    print("Validating filters.yaml against company_details.json...")
    errors = validate_filters_against_company_details(filters_companies, args.company_details, module.slugify)
    if errors:
        print("\nVALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        if args.force:
            print("\n--force given: continuing despite the above.\n")
        else:
            sys.exit(
                "\nAborting before running the fetch. Fix filters.yaml / "
                "company_details.json, or pass --force to run anyway."
            )
    else:
        print("  OK: every company in filters.yaml matches an entry in company_details.json.\n")

    # fetch_tenders_oeffentlichevergabe.py hardcodes its OUTPUT_ROOT relative
    # to its own script location; override it here so results land in
    # backend/tenders regardless of where the fetch module itself lives.
    args.output_dir.mkdir(parents=True, exist_ok=True)
    module.OUTPUT_ROOT = args.output_dir

    module.run(args.target, args.max_days, args.companies, args.filters)


if __name__ == "__main__":
    main()