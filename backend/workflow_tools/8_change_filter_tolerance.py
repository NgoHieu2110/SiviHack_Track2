"""
backend/workflow_tools/8_change_filter_tolerance.py

Called when the user keeps 2 of the 3 tenders they were shown and dismisses
the third. Uses the tolerance the filter had at the moment each of those
three tenders was originally matched (see fetch_tenders_oeffentlichevergabe.py's
"## Filter tolerance at match time" block and tender_index.py's cached
"tolerance" field) to nudge each criterion's tolerance toward what the two
kept tenders had and away from what the removed one had, then re-runs the
pipeline at the new tolerance and hands back one replacement tender.

EXPECTED INPUT (see main.py's RefineTendersRequest)
-----------------------------------------------------
A JSON object with the 3 tenders' full raw markdown (exactly as returned by
5_select_tenders.py / a prior /tenders/match response) and which one of the
three was dismissed:

    {
      "tenders": ["<full md of tender A>", "<full md of tender B>", "<full md of tender C>"],
      "removed_index": 1,          # 0-based index into "tenders"
      "k": 0.5                      # optional, overrides DEFAULT_K
    }

Only removed_index says which one was dismissed -- matching by markdown
content is fragile (whitespace, re-serialization), matching by position
in the array the frontend already has is not. notice_id is still recovered
from each tender's own markdown (same trick 6_user_select_remove_tenders.py
uses), never taken on faith beyond that.

THE FORMULA
------------
For each of the 5 tolerance criteria (cpv, nuts, value, exclude, role_hint),
let a_i, b_i be the tolerance the two KEPT tenders were matched at, and c_i
the tolerance the REMOVED tender was matched at (all normalized 0-1, read
from index.json -- see tender_index.py's "tolerance" field). Then:

    M_i  = (a_i + b_i) / 2
    S_i  = M_i + k * (2*|a_i - b_i| - 1) * (c_i - M_i)

...clamped to [0, 1]. NOTE on direction, since it's easy to misread this
formula on a first pass (I did): the sign of (2*|a_i-b_i| - 1) flips at
|a_i-b_i| = 0.5, not at 0:
  - |a_i-b_i| = 0    (the two kept tenders needed IDENTICAL tolerance):
        factor = -1  -> S_i moves AWAY from c_i, past M_i.
  - |a_i-b_i| = 0.5  -> factor =  0  -> c_i has NO effect; S_i = M_i.
  - |a_i-b_i| = 1    (the two kept tenders needed MAXIMALLY DIFFERENT
        tolerance): factor = +1 -> S_i moves TOWARD c_i.
So the removed tender's tolerance pulls the new setting away from itself
only when the two kept tenders were found at similar tolerance; when the
two kept tenders diverge a lot, S_i is pulled *toward* the removed
tender's tolerance instead, and exactly at |a_i-b_i|=0.5 it's ignored
entirely. This is what the formula as given computes -- flag it if that's
not the intended behavior, since "kept tenders disagree a lot -> lean
toward the removed one" is a non-obvious property to want.

A tender fetched before the "tolerance" field existed has {} for it (see
tender_index.py); any missing criterion falls back to FALLBACK_TOLERANCE
with a printed warning rather than failing the whole request.

WHAT run() ACTUALLY DOES
--------------------------
  1. Recover each of the 3 tenders' notice_id from its markdown.
  2. Look up each one's match-time tolerance from index.json.
  3. Compute the new S_i per criterion.
  4. Dismiss the removed tender (calls 6_user_select_remove_tenders.remove_tender
     -- moves its .md to tenders_seen/, marks it removed in index.json).
  5. Rewrite filters.yaml at the new tolerance (calls
     2_company_details_to_initial_filter.run(), reusing the cached
     ladder/anchors -- no new Gemini call as long as the cache from the
     original filter build is still there).
  6. Re-runs the fetch (calls 3_run_filter_for_tenders.run_filter_for_tenders())
     so new candidates get evaluated against the new, wider/narrower filter
     and index.json's priorities update.
  7. Picks exactly ONE new top-priority tender (calls
     5_select_tenders.select_tenders(count=1)) to replace the one that was
     removed, and returns it alongside the new tolerance.

Importable use:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "change_filter_tolerance", "8_change_filter_tolerance.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    result = mod.change_filter_tolerance(tenders=[md_a, md_b, md_c], removed_index=1)

(The leading digit means this file can't be imported with a plain
`import 8_change_filter_tolerance` statement -- see
1_company_md_to_company_details.py's docstring for why, and the same
importlib pattern applies here.)

Usage:
    python 8_change_filter_tolerance.py \
        --md-file tender_a.md --md-file tender_b.md --md-file tender_c.md \
        --removed-index 1
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

DEFAULT_COMPANY_DETAILS_PATH = SCRIPT_DIR / "company_details.json"
DEFAULT_FILTERS_PATH = SCRIPT_DIR / "filters.yaml"
DEFAULT_FETCH_MODULE_PATH = BACKEND_DIR / "oeffentlichevergabe" / "fetch_tenders_oeffentlichevergabe.py"
DEFAULT_TENDERS_DIR = BACKEND_DIR / "tenders"
DEFAULT_TENDERS_SEEN_DIR = BACKEND_DIR / "tenders_seen"

DEFAULT_TARGET_COUNT = 6
DEFAULT_MAX_DAYS_BACK = 60

CRITERIA = ("cpv", "nuts", "value", "exclude", "role_hint")

# Change constant k in [0, 1]: how strongly the removed tender's tolerance
# is allowed to push S_i away from the midpoint of the two kept tenders'
# tolerance. Overridable per call (function arg / --k / request body field
# in main.py) -- this is only the fallback when nothing else is given.
DEFAULT_K = 0.5

# Fallback tolerance for a criterion whose match-time value is unknown
# (tender predates the "tolerance" field, or that one criterion is
# missing from its block). 0.5 is the same "no strong opinion" default
# 2_company_details_to_initial_filter.py itself falls back to.
FALLBACK_TOLERANCE = 0.5


def _load_module(name: str, path: Path):
    if not path.exists():
        raise FileNotFoundError(f"{name} module not found at {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_filter_module():
    return _load_module("details_to_filter", SCRIPT_DIR / "2_company_details_to_initial_filter.py")


def load_run_filter_module():
    return _load_module("run_filter_for_tenders", SCRIPT_DIR / "3_run_filter_for_tenders.py")


def load_select_module():
    return _load_module("select_tenders", SCRIPT_DIR / "5_select_tenders.py")


def load_remove_module():
    return _load_module("user_select_remove_tenders", SCRIPT_DIR / "6_user_select_remove_tenders.py")


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
    """Same trick as 6_user_select_remove_tenders.py: pull release["id"]
    out of the embedded "## Full raw release JSON" block. Raises
    ValueError if that's not possible."""
    release = tender_index.extract_release_json(markdown)
    notice_id = release.get("id")
    if not notice_id:
        raise ValueError("release JSON in the given markdown has no 'id' field")
    return notice_id


def get_tolerance_for_id(index_data: dict, notice_id: str) -> dict:
    """Cached match-time tolerance for notice_id from index.json (see
    tender_index.py's "tolerance" field), or {} if unindexed/unknown."""
    entry = index_data.get("tenders", {}).get(notice_id, {})
    return entry.get("tolerance") or {}


def resolve_criterion(tol: dict, criterion: str, notice_id: str) -> float:
    """tol[criterion] if present and numeric, else FALLBACK_TOLERANCE with
    a printed warning (never raises -- a single tender with incomplete
    tolerance history shouldn't block the whole request)."""
    val = tol.get(criterion)
    if isinstance(val, (int, float)):
        return float(val)
    print(f"  WARNING: no recorded '{criterion}' tolerance for tender {notice_id}; "
          f"falling back to {FALLBACK_TOLERANCE}")
    return FALLBACK_TOLERANCE


def compute_si(a: float, b: float, c: float, k: float) -> float:
    """S_i = M + k*(2*|a-b| - 1)*(c - M), M = (a+b)/2, clamped to [0, 1].
    See module docstring for the reasoning."""
    m = (a + b) / 2.0
    si = m + k * (2 * abs(a - b) - 1) * (c - m)
    return max(0.0, min(1.0, si))


def compute_new_tolerance(
    kept_tolerances: list,
    removed_tolerance: dict,
    kept_ids: list,
    removed_id: str,
    k: float = DEFAULT_K,
) -> dict:
    """kept_tolerances: [tol_dict_a, tol_dict_b] for the two kept tenders,
    in the same order as kept_ids (used only for warning messages).
    Returns {criterion: S_i} for all of CRITERIA."""
    if not (0.0 <= k <= 1.0):
        raise ValueError(f"k must be in [0, 1], got {k}")
    if len(kept_tolerances) != 2 or len(kept_ids) != 2:
        raise ValueError("compute_new_tolerance expects exactly 2 kept tenders")

    tol_a, tol_b = kept_tolerances
    id_a, id_b = kept_ids

    new_tolerance = {}
    for criterion in CRITERIA:
        a = resolve_criterion(tol_a, criterion, id_a)
        b = resolve_criterion(tol_b, criterion, id_b)
        c = resolve_criterion(removed_tolerance, criterion, removed_id)
        new_tolerance[criterion] = compute_si(a, b, c, k)
    return new_tolerance


def change_filter_tolerance(
    tenders: list,
    removed_index: int,
    k: float = DEFAULT_K,
    company_details_path: Path = DEFAULT_COMPANY_DETAILS_PATH,
    filters_path: Path = DEFAULT_FILTERS_PATH,
    fetch_module_path: Path = DEFAULT_FETCH_MODULE_PATH,
    tenders_dir: Path = DEFAULT_TENDERS_DIR,
    tenders_seen_dir: Path = DEFAULT_TENDERS_SEEN_DIR,
    target: int = DEFAULT_TARGET_COUNT,
    max_days: int = DEFAULT_MAX_DAYS_BACK,
    api_key: str = None,
) -> dict:
    """Library entry point (see module docstring for the full flow).

    `tenders` must have exactly 3 entries (full raw tender markdown, as
    returned by 5_select_tenders.py); `removed_index` (0-2) says which one
    the user dismissed. Returns:

        {
          "removed": {...},              # result of remove_tender()
          "new_tolerance": {...},        # the 5 computed S_i values
          "replacement": {...} | None,   # the one new tender, or None if
                                          # none matched within target/max_days
        }

    Raises ValueError / FileNotFoundError / RuntimeError (never sys.exit)
    so it's safe to call from other code, e.g. a web backend.
    """
    if len(tenders) != 3:
        raise ValueError(f"expected exactly 3 tenders, got {len(tenders)}")
    if removed_index not in (0, 1, 2):
        raise ValueError(f"removed_index must be 0, 1, or 2, got {removed_index}")

    company_details_path = Path(company_details_path)
    filters_path = Path(filters_path)
    fetch_module_path = Path(fetch_module_path)
    tenders_dir = Path(tenders_dir)
    tenders_seen_dir = Path(tenders_seen_dir)

    removed_markdown = tenders[removed_index]
    kept_markdown = [md for i, md in enumerate(tenders) if i != removed_index]

    removed_id = notice_id_from_markdown(removed_markdown)
    kept_ids = [notice_id_from_markdown(md) for md in kept_markdown]

    print(f"Kept:    {kept_ids}")
    print(f"Removed: {removed_id}")

    # --- 1. Read match-time tolerance for all 3 from index.json ------------
    if not tenders_dir.exists():
        raise FileNotFoundError(f"no tenders folder at {tenders_dir}")
    index_data = tender_index.load_index(tenders_dir)

    kept_tolerances = [get_tolerance_for_id(index_data, tid) for tid in kept_ids]
    removed_tolerance = get_tolerance_for_id(index_data, removed_id)

    # --- 2. Compute the new tolerance ---------------------------------------
    new_tolerance = compute_new_tolerance(
        kept_tolerances, removed_tolerance, kept_ids, removed_id, k=k,
    )
    print("New tolerance:")
    for criterion, val in new_tolerance.items():
        print(f"  {criterion}: {val:.4f}")

    # --- 3. Dismiss the removed tender ---------------------------------------
    remove_module = load_remove_module()
    removed_result = remove_module.remove_tender(
        markdown=removed_markdown,
        tenders_dir=tenders_dir,
        tenders_seen_dir=tenders_seen_dir,
    )
    print(f"Removed: {removed_result}")

    # --- 4. Rewrite filters.yaml at the new tolerance -----------------------
    # Reuses build_filters_yaml's cache (keyed by company name) -- no new
    # Gemini call as long as the cache from the original filter build is
    # still on disk next to filters.yaml.
    filter_module = load_filter_module()
    filter_module.run(
        input_path=str(company_details_path),
        out_path=str(filters_path),
        tolerance_cpv=new_tolerance["cpv"],
        tolerance_nuts=new_tolerance["nuts"],
        tolerance_value=new_tolerance["value"],
        tolerance_exclude=new_tolerance["exclude"],
        tolerance_role_hint=new_tolerance["role_hint"],
        api_key=api_key,
    )

    # --- 5. Re-fetch at the new tolerance, updating index.json -------------
    run_filter_module = load_run_filter_module()
    run_filter_module.run_filter_for_tenders(
        filters_path=filters_path,
        fetch_module_path=fetch_module_path,
        output_dir=tenders_dir,
        tenders_seen_dir=tenders_seen_dir,
        target=target,
        max_days=max_days,
    )

    # --- 6. Pick exactly one replacement ------------------------------------
    select_module = load_select_module()
    try:
        replacement_list = select_module.select_tenders(count=1, tenders_dir=tenders_dir)
    except (FileNotFoundError, ValueError) as e:
        print(f"  No replacement tender available: {e}")
        replacement_list = []

    replacement = replacement_list[0] if replacement_list else None

    return {
        "removed": removed_result,
        "new_tolerance": new_tolerance,
        "replacement": replacement,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--md-file", action="append", required=True, dest="md_files",
                         help="Path to a tender's raw markdown. Pass exactly 3 (repeat the flag).")
    parser.add_argument("--removed-index", type=int, required=True,
                         help="0-based index into the 3 --md-file flags, in the order given, "
                              "of the tender that was dismissed.")
    parser.add_argument("--k", type=float, default=DEFAULT_K, help=f"Change constant (default: {DEFAULT_K})")
    parser.add_argument("--company-details", type=Path, default=DEFAULT_COMPANY_DETAILS_PATH)
    parser.add_argument("--filters", type=Path, default=DEFAULT_FILTERS_PATH)
    parser.add_argument("--fetch-module", type=Path, default=DEFAULT_FETCH_MODULE_PATH)
    parser.add_argument("--tenders-dir", type=Path, default=DEFAULT_TENDERS_DIR)
    parser.add_argument("--tenders-seen-dir", type=Path, default=DEFAULT_TENDERS_SEEN_DIR)
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET_COUNT)
    parser.add_argument("--max-days", type=int, default=DEFAULT_MAX_DAYS_BACK)
    args = parser.parse_args()

    if len(args.md_files) != 3:
        sys.exit(f"ERROR: expected exactly 3 --md-file flags, got {len(args.md_files)}")

    tenders = []
    for p in args.md_files:
        path = Path(p)
        if not path.exists():
            sys.exit(f"ERROR: --md-file not found: {path}")
        tenders.append(path.read_text(encoding="utf-8"))

    try:
        result = change_filter_tolerance(
            tenders=tenders,
            removed_index=args.removed_index,
            k=args.k,
            company_details_path=args.company_details,
            filters_path=args.filters,
            fetch_module_path=args.fetch_module,
            tenders_dir=args.tenders_dir,
            tenders_seen_dir=args.tenders_seen_dir,
            target=args.target,
            max_days=args.max_days,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        sys.exit(f"ERROR: {e}")

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()