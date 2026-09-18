#!/usr/bin/env python3
"""
backend/workflow_tools/2_company_details_to_initial_filter.py

Converts company_details.json (see 1_company_md_to_company_details.py) into
an initial filters.yaml for fetch_tenders_oeffentlichevergabe.py.

WHY THIS IS HARD TO DO DETERMINISTICALLY
-----------------------------------------
Two of the required fields, cpv_prefixes and nuts_prefixes, require domain
judgment ("road construction, sewers" -> which CPV prefixes; "Bavaria, 150km
from Augsburg" -> which NUTS prefixes), so this script asks Gemini to do
that mapping per company.

TOLERANCE / SOFTNESS
---------------------
Every tunable filter criterion has its own tolerance dial in [0.0, 1.0],
which is the INVERSE of filter strength:
    tolerance 0.0  -> as strict/true to company_details.json as possible
    tolerance 1.0  -> essentially no filtering on that criterion
Five independently settable dials:
    --tolerance-cpv         (default: --tolerance)
    --tolerance-nuts        (default: --tolerance)
    --tolerance-value       (default: --tolerance)
    --tolerance-exclude     (default: --tolerance)   ! see warning below
    --tolerance-role-hint   (default: --tolerance)
--tolerance sets the fallback used for any dial not given explicitly
(default 0.5).

! exclude_keywords represents genuine hard capability limits (e.g. "no rail
  work", "no high voltage") stated directly in company_details.json's
  "exclusions" field, not soft preferences. Softening it (tolerance > 0)
  will let tenders through that the company explicitly said it cannot do.
  It has a dial because every criterion should have one, but 0.0 is the
  recommended value for it unless you have a specific reason to loosen it.

HOW EACH DIAL IS APPLIED
--------------------------
cpv_prefixes, nuts_prefixes, role_hint_reject, exclude_keywords are "is this
code/phrase in or out" filters, so Gemini generates a LADDER: a concrete
list at each of six tolerance steps (0.0, 0.2, 0.4, 0.6, 0.8, 1.0). The
requested tolerance is snapped to the nearest step and that step's list is
used as-is.

value_min / value_max are continuous, so Gemini instead gives a "tight"
anchor (~tolerance 0.0, the company's real stated band) and a "loose" anchor
(~tolerance 1.0, effectively unbounded), and this script linearly
interpolates between them for the requested tolerance.

CACHING
--------
Gemini is called once per company; the raw ladder/anchor response is cached
to --cache-path (default: .filter_ladders_cache.json, next to --out) keyed
by company name. Re-running with different tolerance values re-uses the
cache and needs no further API calls. Pass --refresh to force new calls
(e.g. after company_details.json content changes).

Usage:
    export GEMINI_API_KEY="your-key-here"
    python 2_company_details_to_initial_filter.py \
        --input company_details.json --out filters.yaml \
        --tolerance 0.3 --tolerance-exclude 0.0 --tolerance-role-hint 0.7
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"
GEMINI_ENDPOINT_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

TOLERANCE_STEPS = ["0.0", "0.2", "0.4", "0.6", "0.8", "1.0"]

NUTS_REFERENCE = """\
NUTS reference for Germany (use these top-level codes, or a longer/more
specific sub-code such as DE21 or DE27 for a tighter regional fit):
  DE1 Baden-Wuerttemberg   DE6 Hamburg
  DE2 Bayern               DE7 Hessen
  DE3 Berlin               DE8 Mecklenburg-Vorpommern
  DE4 Brandenburg          DE9 Niedersachsen
  DE5 Bremen               DEA Nordrhein-Westfalen
  DEB Rheinland-Pfalz      DEC Saarland
  DED Sachsen              DEE Sachsen-Anhalt
  DEF Schleswig-Holstein   DEG Thueringen
"""

PROMPT_TEMPLATE = """\
You are helping configure a German public-tender matching filter for a
construction/engineering company. Use CPV codes (EU Common Procurement
Vocabulary, https://simap.ted.europa.eu/cpv) and NUTS region codes.

{nuts_reference}

COMPANY PROFILE:
  Name: {name}
  Short tag: {description}
  What they do: {does}
  Place of performance / operating area: {place_of_performance}
  Stated minimum viable contract value (EUR): {value_min}
  Stated maximum they could handle (EUR): {value_max}
  Stated exclusions (things they CANNOT or WILL NOT do): {exclusions}
  Other specifications (financial limits, capacity, reference projects,
  quotes about what kind of work fits them): {specifications}

Return ONLY a single JSON object (no markdown fences, no commentary) with
exactly this shape:

{{
  "cpv_ladder": {{
    "0.0": [{{"code": "CPV_PREFIX", "label": "short description"}}, ...],
    "0.2": [...], "0.4": [...], "0.6": [...], "0.8": [...], "1.0": [...]
  }},
  "nuts_ladder": {{
    "0.0": [{{"code": "NUTS_PREFIX", "label": "short description"}}, ...],
    "0.2": [...], "0.4": [...], "0.6": [...], "0.8": [...], "1.0": [...]
  }},
  "exclude_keywords_ladder": {{
    "0.0": ["keyword1", "keyword2", ...],
    "0.2": [...], "0.4": [...], "0.6": [...], "0.8": [...], "1.0": []
  }},
  "role_hint_ladder": {{
    "0.0": ["phrase1", "phrase2", ...],
    "0.2": [...], "0.4": [...], "0.6": [...], "0.8": [...], "1.0": []
  }},
  "value_min_tight": number,
  "value_min_loose": number,
  "value_max_tight": number,
  "value_max_loose": number,
  "notes": "one or two sentence summary of this company for a human reading the filter file"
}}

LADDER RULES (apply the same logic to cpv_ladder, nuts_ladder,
exclude_keywords_ladder, and role_hint_ladder):
- "0.0" is the strictest / narrowest list: only codes or keywords that are
  clearly, directly justified by the profile above.
- "1.0" is always an empty list [] (no filtering at all on that criterion).
- Steps in between progressively broaden: 0.2 adds a little breadth beyond
  0.0, 0.4 more, etc., ending at the empty list by 1.0. Each step's list
  should be a superset-ish broadening of the previous step's intent (for
  keyword ladders specifically: keywords should tend to DISAPPEAR as the
  step number rises, since removing an exclude/role-hint keyword is what
  "loosening" means for those two ladders specifically -- so for
  exclude_keywords_ladder and role_hint_ladder, treat 0.0 as the FULL list
  of everything justified by "exclusions"/quotes in the profile, and each
  higher step as progressively dropping the weakest/most speculative
  entries, down to [] at 1.0).
- For cpv_ladder and nuts_ladder, broadening means using shorter/broader
  prefixes or adding adjacent/parent categories at higher steps (e.g. a
  specific 6-digit CPV code at 0.0 might broaden to its 3-digit parent
  prefix by 0.6), NOT dropping entries -- since these are membership tests
  where broader prefixes match MORE tenders, which is what "loosening"
  means for CPV/NUTS specifically.
- Every step 0.0 through 0.8 for cpv_ladder and nuts_ladder must be
  non-empty (a tender can't match an empty CPV or region list at all).

NUMERIC RULES:
- value_min_tight / value_max_tight should reflect the company's stated
  min/max as closely as the profile allows.
- value_min_loose should be a small number close to 0 (e.g. 0 or a token
  minimum).
- value_max_loose should be a very large number effectively removing the
  ceiling (e.g. 10x-50x the stated max, or higher for very small companies).

Return raw JSON only.
"""


def call_gemini(prompt: str, api_key: str, model: str) -> dict:
    url = GEMINI_ENDPOINT_TEMPLATE.format(model=model)
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Gemini API error {e.code}: {e.read().decode('utf-8', errors='replace')}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not reach Gemini API: {e}") from e

    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini response shape: {json.dumps(body)[:500]}") from e

    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Could not parse JSON from Gemini output:\n{cleaned}") from e


def slugify(name: str) -> str:
    """Identical to fetch_tenders.py's slugify() so keys line up."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def build_prompt(company: dict) -> str:
    return PROMPT_TEMPLATE.format(
        nuts_reference=NUTS_REFERENCE,
        name=company.get("name", ""),
        description=company.get("description", company.get("contractNature", "")),
        does=company.get("does", ""),
        place_of_performance=company.get("placeOfPerformance", ""),
        value_min=company.get("contractValueMin", "unknown"),
        value_max=company.get("contractValueMax", "unknown"),
        exclusions=company.get("exclusions", ""),
        specifications=company.get("specifications", ""),
    )


def load_cache(cache_path: str) -> dict:
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_cache(cache_path: str, cache: dict):
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def validate_ladder(ladder: dict, name: str, allow_empty_at_1_0_only: bool):
    for step in TOLERANCE_STEPS:
        if step not in ladder:
            raise RuntimeError(f"{name}: missing tolerance step '{step}' in Gemini response")
        if step != "1.0" and allow_empty_at_1_0_only and not ladder[step]:
            raise RuntimeError(f"{name}: tolerance step '{step}' is empty (only 1.0 may be empty)")


def snap_step(t: float) -> str:
    steps_f = [float(s) for s in TOLERANCE_STEPS]
    closest = min(steps_f, key=lambda s: abs(s - t))
    return f"{closest:.1f}"


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def resolve_code_list(ladder: dict, t: float):
    """cpv/nuts ladders: list of {code, label} dicts at the snapped step."""
    step = snap_step(t)
    entries = ladder[step]
    codes = [e["code"] for e in entries]
    return codes, entries, step


def resolve_keyword_list(ladder: dict, t: float):
    step = snap_step(t)
    return ladder[step], step


def yaml_str(s: str) -> str:
    """Double-quote a string for safe YAML embedding."""
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_company_block(key: str, company: dict, ladders: dict, tol: dict) -> str:
    lines = []
    lines.append(f"{key}:")
    lines.append(f"  display_name: {yaml_str(company.get('name', key))}")
    lines.append("")

    cpv_codes, cpv_entries, cpv_step = resolve_code_list(ladders["cpv_ladder"], tol["cpv"])
    lines.append(f"  # cpv_prefixes (tolerance={tol['cpv']:.2f}, snapped to step {cpv_step})")
    lines.append("  cpv_prefixes:")
    for e in cpv_entries:
        lines.append(f"    - {yaml_str(e['code'])}  # {e.get('label', '')}")
    lines.append("")

    nuts_codes, nuts_entries, nuts_step = resolve_code_list(ladders["nuts_ladder"], tol["nuts"])
    lines.append(f"  # nuts_prefixes (tolerance={tol['nuts']:.2f}, snapped to step {nuts_step})")
    lines.append("  nuts_prefixes:")
    for e in nuts_entries:
        lines.append(f"    - {yaml_str(e['code'])}  # {e.get('label', '')}")
    lines.append("")

    vmin = lerp(ladders["value_min_tight"], ladders["value_min_loose"], tol["value"])
    vmax = lerp(ladders["value_max_tight"], ladders["value_max_loose"], tol["value"])
    lines.append(f"  # value_min / value_max (tolerance={tol['value']:.2f}, interpolated between")
    lines.append(f"  # tight [{ladders['value_min_tight']:,.0f}, {ladders['value_max_tight']:,.0f}] and")
    lines.append(f"  # loose [{ladders['value_min_loose']:,.0f}, {ladders['value_max_loose']:,.0f}])")
    lines.append(f"  value_min: {vmin:.0f}")
    lines.append(f"  value_max: {vmax:.0f}")
    lines.append("")

    excl_list, excl_step = resolve_keyword_list(ladders["exclude_keywords_ladder"], tol["exclude"])
    warn = "  # NOTE: tolerance > 0 here means real stated exclusions are being dropped." if tol["exclude"] > 0 else ""
    lines.append(f"  # exclude_keywords (tolerance={tol['exclude']:.2f}, snapped to step {excl_step}){warn}")
    if excl_list:
        lines.append("  exclude_keywords:")
        for kw in excl_list:
            lines.append(f"    - {yaml_str(kw)}")
    else:
        lines.append("  exclude_keywords: []")
    lines.append("")

    role_list, role_step = resolve_keyword_list(ladders["role_hint_ladder"], tol["role_hint"])
    lines.append(f"  # role_hint_reject (tolerance={tol['role_hint']:.2f}, snapped to step {role_step})")
    if role_list:
        lines.append("  role_hint_reject:")
        for kw in role_list:
            lines.append(f"    - {yaml_str(kw)}")
    else:
        lines.append("  role_hint_reject: []")
    lines.append("")

    lines.append("  # Newer optional fields (procurement_methods_allowed, min_bid_prep_days,")
    lines.append("  # reject_reserved_participation, contract_starts_after/_before) are left")
    lines.append("  # unset here -- company_details.json doesn't carry enough signal to set")
    lines.append("  # them confidently. Uncomment and tune by hand once real match volume exists.")
    lines.append("  # procurement_methods_allowed: [\"open\", \"restricted\"]")
    lines.append("  # min_bid_prep_days: 10")
    lines.append("  # reject_reserved_participation: false")
    lines.append("  # contract_starts_after: null")
    lines.append("  # contract_starts_before: null")
    lines.append("")

    notes = ladders.get("notes", "").strip()
    tol_summary = (
        f"[Generated at tolerance: cpv={tol['cpv']:.2f}, nuts={tol['nuts']:.2f}, "
        f"value={tol['value']:.2f}, exclude={tol['exclude']:.2f}, role_hint={tol['role_hint']:.2f}]"
    )
    full_notes = f"{notes} {tol_summary}".strip()
    lines.append(f"  notes: {yaml_str(full_notes)}")

    return "\n".join(lines)


def render_header(tol_defaults: dict) -> str:
    return f"""\
# ============================================================================
# filters.yaml — AUTO-GENERATED by 2_company_details_to_initial_filter.py
# ============================================================================
# Generated from company_details.json. This file is plain YAML and safe to
# hand-edit afterward; re-running the generator script will overwrite it
# completely, so save manual tweaks elsewhere if you want to keep them.
#
# TOLERANCE (see script docstring for full details): every criterion below
# was produced at its own tolerance in [0.0, 1.0], the inverse of filter
# strength (0.0 = strict/true to company_details.json, 1.0 = no filtering
# on that criterion). Defaults used for this run unless overridden per
# company/criterion:
#   cpv={tol_defaults['cpv']:.2f}  nuts={tol_defaults['nuts']:.2f}  value={tol_defaults['value']:.2f}  \
exclude={tol_defaults['exclude']:.2f}  role_hint={tol_defaults['role_hint']:.2f}
# NOTE: exclude_keywords represents genuine hard capability limits (things
# the company explicitly said it cannot/will not do). A tolerance above 0.0
# there means real exclusions are being dropped -- recommended default is
# --tolerance-exclude 0.0 unless you have a specific reason to loosen it.
#
# See fetch_tenders.py / the original filters.yaml for the full field
# reference (cpv_prefixes, nuts_prefixes, value_min/max, exclude_keywords,
# role_hint_reject, and the newer optional fields).
# -----------------------------------------------------------------------------

"""


def main():
    parser = argparse.ArgumentParser(description="Convert company_details.json into filters.yaml via Gemini, with a per-criterion tolerance dial.")
    parser.add_argument("--input", default="company_details.json", help="Path to company_details.json (default: company_details.json)")
    parser.add_argument("--out", default="filters.yaml", help="Output filters.yaml path (default: filters.yaml)")
    parser.add_argument("--model", default=GEMINI_MODEL_DEFAULT, help=f"Gemini model (default: {GEMINI_MODEL_DEFAULT})")
    parser.add_argument("--cache-path", default=None, help="Cache file for raw Gemini ladders (default: .filter_ladders_cache.json next to --out)")
    parser.add_argument("--refresh", action="store_true", help="Ignore cache and re-call Gemini for every company")
    parser.add_argument("--companies", nargs="*", default=None, help="Restrict to company names containing these substrings (default: all)")

    parser.add_argument("--tolerance", type=float, default=0.5, help="Global default tolerance in [0,1] for any dial not set explicitly (default: 0.5)")
    parser.add_argument("--tolerance-cpv", type=float, default=None)
    parser.add_argument("--tolerance-nuts", type=float, default=None)
    parser.add_argument("--tolerance-value", type=float, default=None)
    parser.add_argument("--tolerance-exclude", type=float, default=None)
    parser.add_argument("--tolerance-role-hint", type=float, default=None)
    args = parser.parse_args()

    for name, val in [("--tolerance", args.tolerance), ("--tolerance-cpv", args.tolerance_cpv),
                       ("--tolerance-nuts", args.tolerance_nuts), ("--tolerance-value", args.tolerance_value),
                       ("--tolerance-exclude", args.tolerance_exclude), ("--tolerance-role-hint", args.tolerance_role_hint)]:
        if val is not None and not (0.0 <= val <= 1.0):
            sys.exit(f"ERROR: {name} must be in [0.0, 1.0], got {val}")

    tol_defaults = {
        "cpv": args.tolerance_cpv if args.tolerance_cpv is not None else args.tolerance,
        "nuts": args.tolerance_nuts if args.tolerance_nuts is not None else args.tolerance,
        "value": args.tolerance_value if args.tolerance_value is not None else args.tolerance,
        "exclude": args.tolerance_exclude if args.tolerance_exclude is not None else args.tolerance,
        "role_hint": args.tolerance_role_hint if args.tolerance_role_hint is not None else args.tolerance,
    }

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("ERROR: set the GEMINI_API_KEY environment variable before running this script.\n  export GEMINI_API_KEY=\"your-key-here\"")

    if not os.path.exists(args.input):
        sys.exit(f"ERROR: input file not found: {args.input}")

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_companies = data.get("companies", [])
    if not all_companies:
        sys.exit(f"ERROR: no companies found in {args.input} (expected {{\"companies\": [...]}})")

    if args.companies:
        wanted = [c.lower() for c in args.companies]
        all_companies = [c for c in all_companies if any(w in c.get("name", "").lower() for w in wanted)]
        if not all_companies:
            sys.exit(f"ERROR: no companies matched --companies filter {args.companies}")

    cache_path = args.cache_path or os.path.join(os.path.dirname(os.path.abspath(args.out)) or ".", ".filter_ladders_cache.json")
    cache = {} if args.refresh else load_cache(cache_path)

    blocks = []
    for company in all_companies:
        name = company.get("name", "unnamed")
        key = slugify(name)

        if name in cache and not args.refresh:
            print(f"{name}: using cached ladder ({cache_path})")
            ladders = cache[name]
        else:
            print(f"{name}: calling Gemini ({args.model}) to build filter ladder...")
            prompt = build_prompt(company)
            ladders = call_gemini(prompt, api_key, args.model)
            cache[name] = ladders
            save_cache(cache_path, cache)

        validate_ladder(ladders["cpv_ladder"], f"{name} cpv_ladder", allow_empty_at_1_0_only=True)
        validate_ladder(ladders["nuts_ladder"], f"{name} nuts_ladder", allow_empty_at_1_0_only=True)
        validate_ladder(ladders["exclude_keywords_ladder"], f"{name} exclude_keywords_ladder", allow_empty_at_1_0_only=False)
        validate_ladder(ladders["role_hint_ladder"], f"{name} role_hint_ladder", allow_empty_at_1_0_only=False)

        block = render_company_block(key, company, ladders, tol_defaults)
        blocks.append(block)
        print(f"  -> resolved block for key '{key}'")

    output = render_header(tol_defaults) + "\n\n".join(blocks) + "\n"

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\nWrote {args.out} with {len(blocks)} company block(s).")
    print(f"Ladder cache: {cache_path} (re-run with different --tolerance-* flags without re-calling Gemini)")


if __name__ == "__main__":
    main()