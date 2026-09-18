#!/usr/bin/env python3
"""
backend/workflow_tools/2_company_details_to_initial_filter.py

Converts company_details.json (see 1_company_md_to_company_details.py) into
an initial filters.yaml for fetch_tenders_oeffentlichevergabe.py.

company_details.json holds a single flat company object (one company per
backend instance, not a list) -- e.g.:

    {
      "name": "...", "description": "...", "does": "...",
      "placeOfPerformance": "...", "contractValueMin": ..., ...
    }

and the filters.yaml this produces is likewise a single flat block of
filter fields, with no company-key wrapper around it.

Importable use:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "details_to_filter", "2_company_details_to_initial_filter.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    output_text = mod.run(
        input_path="company_details.json",
        out_path="filters.yaml",
        tolerance=0.3,
        tolerance_exclude=0.0,
        tolerance_role_hint=0.7,
    )

(The leading digit means this file can't be imported with a plain
`import 2_company_details_to_initial_filter` statement -- see
1_company_md_to_company_details.py's docstring for why, and the same
importlib pattern applies here.)

WHY THIS IS HARD TO DO DETERMINISTICALLY
-----------------------------------------
Two of the required fields, cpv_prefixes and nuts_prefixes, require domain
judgment ("road construction, sewers" -> which CPV prefixes; "Bavaria, 150km
from Augsburg" -> which NUTS prefixes), so this script asks Claude to do
that mapping.

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

The five resolved dial values are written into filters.yaml itself as a
real `tolerance:` field (not just the header comment), so downstream
scripts (fetch_tenders_oeffentlichevergabe.py, 8_change_filter_tolerance.py)
can read back exactly what tolerance produced a given filter run.

! exclude_keywords represents genuine hard capability limits (e.g. "no rail
  work", "no high voltage") stated directly in company_details.json's
  "exclusions" field, not soft preferences. Softening it (tolerance > 0)
  will let tenders through that the company explicitly said it cannot do.
  It has a dial because every criterion should have one, but 0.0 is the
  recommended value for it unless you have a specific reason to loosen it.

HOW EACH DIAL IS APPLIED
--------------------------
cpv_prefixes, nuts_prefixes, role_hint_reject, exclude_keywords are "is this
code/phrase in or out" filters, so Claude generates a LADDER: a concrete
list at each of six tolerance steps (0.0, 0.2, 0.4, 0.6, 0.8, 1.0). The
requested tolerance is snapped to the nearest step and that step's list is
used as-is.

value_min / value_max are continuous, so Claude instead gives a "tight"
anchor (~tolerance 0.0, the company's real stated band) and a "loose" anchor
(~tolerance 1.0, effectively unbounded), and this script linearly
interpolates between them for the requested tolerance.

MATCH_MODE / MIN_CRITERIA_MATCHED (loosening the AND logic itself)
--------------------------------------------------------------------
Widening the ladders above only helps if fetch_tenders_oeffentlichevergabe.py's
matches_profile() is willing to accept a tender that satisfies some but not
all of CPV/region/value. That's controlled by two new filters.yaml fields,
written by this script and derived automatically unless overridden:
    --match-mode {auto,all,any}       (default: auto)
    --min-criteria-matched N          (only used when match_mode is "any")
"all" is the original strict AND. "any" accepts a tender if at least N of
the *considered* core criteria (CPV/region/value -- whichever have a filter
actually set) match, even if the rest don't. "auto" derives all/any and N
from how loose the cpv/nuts/value tolerance dials already are -- see
resolve_match_mode()'s docstring for the exact thresholds. exclude_keywords
and role_hint_reject are never softened by this; they stay a hard reject.

CACHING
--------
Claude is called once; the raw ladder/anchor response is cached to
--cache-path (default: .filter_ladders_cache.json, next to --out) keyed by
company name. Re-running with different tolerance values re-uses the cache
and needs no further API calls. Pass --refresh to force a new call (e.g.
after company_details.json content changes).

Usage:
    export ANTHROPIC_API_KEY="your-key-here"   # or set it in backend/.env
    python 2_company_details_to_initial_filter.py \
        --input company_details.json --out filters.yaml \
        --tolerance 0.3 --tolerance-exclude 0.0 --tolerance-role-hint 0.7

    # Broader ladders AND soft AND-logic (recommended for "too strict"):
    python 2_company_details_to_initial_filter.py \
        --tolerance 0.6 --tolerance-exclude 0.0 \
        --match-mode any --min-criteria-matched 2
"""

import argparse
import hashlib
import json
import os
import re
import sys

import anthropic

from common import get_anthropic_api_key

CLAUDE_MODEL_DEFAULT = "claude-opus-5"

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
- Don't just narrow the SAME division at every step. From 0.4 upward, also
  add plausibly-relevant codes from NEIGHBORING divisions/categories that
  this kind of company could realistically bid on, subcontract into, or
  team up on, even if they're not the company's core trade (e.g. a
  structural-engineering firm's ladder should reach into general civil
  works, related site-prep/earthworks, and adjacent technical-consulting
  codes by 0.6-0.8, not just broader prefixes of its own exact niche).
  Likewise for nuts_ladder from 0.4 upward, add neighboring/adjacent NUTS
  regions the company could plausibly travel to or open a temporary site
  in, not only broader prefixes containing its own region. Because
  matches_profile() can now be configured (via match_mode/
  min_criteria_matched, see below) to accept a tender that only satisfies
  SOME of CPV/region/value rather than all of them, it is fine -- and
  intended -- for the 0.6-0.8 lists to include codes/regions that are only
  loosely related to the core profile; the match_mode setting is what
  keeps an unrelated-but-CPV-matching or unrelated-but-region-matching
  tender from being an automatic reject.
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


def call_claude(prompt: str, api_key: str, model: str) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}") from e

    text = "".join(block.text for block in response.content if block.type == "text")
    if not text:
        raise RuntimeError("Claude returned an empty response.")

    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Could not parse JSON from Claude output:\n{cleaned}") from e


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


def compute_cache_key(company: dict) -> str:
    """Cache key derived from the exact fields fed into the Claude prompt
    (see build_prompt()) -- NOT from company.get('name').

    Bug this fixes: company_details.json doesn't always carry a 'name'
    field. The cache used to be keyed on `company.get("name", "unnamed")`,
    so any two companies that both lacked a 'name' (or happened to share
    one) collided on the same cache entry -- whichever ran second silently
    got the first company's ladder (wrong CPV codes, wrong NUTS region,
    wrong value band), even though its own company_details.json was
    completely different. Hashing the actual prompt-relevant fields means
    two different profiles can never collide, regardless of what 'name'
    is or isn't set to, and the SAME profile re-run still hits the cache
    (same fields -> same hash) so tolerance-only re-runs still cost zero
    extra Claude calls.
    """
    fields = {
        "name": company.get("name", ""),
        "description": company.get("description", company.get("contractNature", "")),
        "does": company.get("does", ""),
        "placeOfPerformance": company.get("placeOfPerformance", ""),
        "contractValueMin": company.get("contractValueMin", ""),
        "contractValueMax": company.get("contractValueMax", ""),
        "exclusions": company.get("exclusions", ""),
        "specifications": company.get("specifications", ""),
    }
    canonical = json.dumps(fields, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


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
            raise RuntimeError(f"{name}: missing tolerance step '{step}' in Claude response")
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


def render_filters_body(
    company: dict,
    ladders: dict,
    tol: dict,
    match_mode: str = "auto",
    min_criteria_matched: int = None,
) -> str:
    """Renders the flat filters.yaml body -- top-level fields, no
    company-key wrapper (there's only ever one company/profile)."""
    lines = []
    lines.append(f"display_name: {yaml_str(company.get('name', 'company'))}")
    lines.append("")

    # Machine-readable record of the exact per-criterion tolerance dials
    # used to produce this filters.yaml. Unlike the human-readable summary
    # in the header comment, this block is a real YAML field that
    # fetch_tenders_oeffentlichevergabe.py reads and stamps onto every
    # tender it matches under this filter (see that script's
    # OPTIONAL_FIELD_DEFAULTS / render_markdown()), so each tender's own
    # .md records which tolerance it was found under. That, in turn, is
    # what 8_change_filter_tolerance.py reads back out of index.json to
    # compute a new tolerance from a kept/removed tender comparison -- see
    # that script's docstring.
    lines.append("# Exact tolerance dials used to build this file (machine-readable;")
    lines.append("# do not remove -- downstream scripts depend on this block).")
    lines.append("tolerance:")
    lines.append(f"  cpv: {tol['cpv']:.4f}")
    lines.append(f"  nuts: {tol['nuts']:.4f}")
    lines.append(f"  value: {tol['value']:.4f}")
    lines.append(f"  exclude: {tol['exclude']:.4f}")
    lines.append(f"  role_hint: {tol['role_hint']:.4f}")
    lines.append("")

    cpv_codes, cpv_entries, cpv_step = resolve_code_list(ladders["cpv_ladder"], tol["cpv"])
    lines.append(f"# cpv_prefixes (tolerance={tol['cpv']:.2f}, snapped to step {cpv_step})")
    lines.append("cpv_prefixes:")
    for e in cpv_entries:
        lines.append(f"  - {yaml_str(e['code'])}  # {e.get('label', '')}")
    lines.append("")

    nuts_codes, nuts_entries, nuts_step = resolve_code_list(ladders["nuts_ladder"], tol["nuts"])
    lines.append(f"# nuts_prefixes (tolerance={tol['nuts']:.2f}, snapped to step {nuts_step})")
    lines.append("nuts_prefixes:")
    for e in nuts_entries:
        lines.append(f"  - {yaml_str(e['code'])}  # {e.get('label', '')}")
    lines.append("")

    vmin = lerp(ladders["value_min_tight"], ladders["value_min_loose"], tol["value"])
    vmax = lerp(ladders["value_max_tight"], ladders["value_max_loose"], tol["value"])
    lines.append(f"# value_min / value_max (tolerance={tol['value']:.2f}, interpolated between")
    lines.append(f"# tight [{ladders['value_min_tight']:,.0f}, {ladders['value_max_tight']:,.0f}] and")
    lines.append(f"# loose [{ladders['value_min_loose']:,.0f}, {ladders['value_max_loose']:,.0f}])")
    lines.append(f"value_min: {vmin:.0f}")
    lines.append(f"value_max: {vmax:.0f}")
    lines.append("")

    resolved_mode, resolved_min, mode_avg = resolve_match_mode(tol, match_mode, min_criteria_matched)
    avg_note = f", avg core tolerance {mode_avg:.2f}" if mode_avg is not None else " (explicitly forced)"
    lines.append(f"# match_mode (resolved from --match-mode={match_mode}{avg_note}):")
    lines.append("#   \"all\" -> strict AND: a tender must satisfy every one of CPV/region/")
    lines.append("#            value that has a filter set (the original, pre-broadening")
    lines.append("#            behavior).")
    lines.append("#   \"any\" -> soft match: a tender passes if at least")
    lines.append("#            min_criteria_matched of the *considered* CPV/region/value")
    lines.append("#            criteria pass, even if the rest miss. This is what lets")
    lines.append("#            through tenders only partially related to the profile.")
    lines.append("# exclude_keywords / role_hint_reject are NEVER softened by this -- they")
    lines.append("# stay a hard reject in either mode. See matches_profile() in")
    lines.append("# fetch_tenders_oeffentlichevergabe.py for the exact rules.")
    lines.append(f"match_mode: {yaml_str(resolved_mode)}")
    lines.append(f"min_criteria_matched: {resolved_min if resolved_min is not None else 'null'}")
    lines.append("")

    excl_list, excl_step = resolve_keyword_list(ladders["exclude_keywords_ladder"], tol["exclude"])
    warn = "  # NOTE: tolerance > 0 here means real stated exclusions are being dropped." if tol["exclude"] > 0 else ""
    lines.append(f"# exclude_keywords (tolerance={tol['exclude']:.2f}, snapped to step {excl_step}){warn}")
    if excl_list:
        lines.append("exclude_keywords:")
        for kw in excl_list:
            lines.append(f"  - {yaml_str(kw)}")
    else:
        lines.append("exclude_keywords: []")
    lines.append("")

    role_list, role_step = resolve_keyword_list(ladders["role_hint_ladder"], tol["role_hint"])
    lines.append(f"# role_hint_reject (tolerance={tol['role_hint']:.2f}, snapped to step {role_step})")
    if role_list:
        lines.append("role_hint_reject:")
        for kw in role_list:
            lines.append(f"  - {yaml_str(kw)}")
    else:
        lines.append("role_hint_reject: []")
    lines.append("")

    lines.append("# Newer optional fields (procurement_methods_allowed, min_bid_prep_days,")
    lines.append("# reject_reserved_participation, contract_starts_after/_before) are left")
    lines.append("# unset here -- company_details.json doesn't carry enough signal to set")
    lines.append("# them confidently. Uncomment and tune by hand once real match volume exists.")
    lines.append("# procurement_methods_allowed: [\"open\", \"restricted\"]")
    lines.append("# min_bid_prep_days: 10")
    lines.append("# reject_reserved_participation: false")
    lines.append("# contract_starts_after: null")
    lines.append("# contract_starts_before: null")
    lines.append("")

    notes = ladders.get("notes", "").strip()
    tol_summary = (
        f"[Generated at tolerance: cpv={tol['cpv']:.2f}, nuts={tol['nuts']:.2f}, "
        f"value={tol['value']:.2f}, exclude={tol['exclude']:.2f}, role_hint={tol['role_hint']:.2f}]"
    )
    full_notes = f"{notes} {tol_summary}".strip()
    lines.append(f"notes: {yaml_str(full_notes)}")

    return "\n".join(lines)


def render_header(tol_defaults: dict, cache_key: str = None) -> str:
    key_line = (
        f"# Ladder cache key: {cache_key}  (see .filter_ladders_cache.json --\n"
        f"# if this filters.yaml ever looks wrong for the company it was built\n"
        f"# from, check whether this key collides with another company's entry)\n#\n"
        if cache_key else ""
    )
    return f"""\
# ============================================================================
# filters.yaml — AUTO-GENERATED by 2_company_details_to_initial_filter.py
# ============================================================================
# Generated from company_details.json. This file is plain YAML and safe to
# hand-edit afterward; re-running the generator script will overwrite it
# completely, so save manual tweaks elsewhere if you want to keep them.
#
{key_line}# TOLERANCE (see script docstring for full details): every criterion below
# was produced at its own tolerance in [0.0, 1.0], the inverse of filter
# strength (0.0 = strict/true to company_details.json, 1.0 = no filtering
# on that criterion). Defaults used for this run unless overridden per
# criterion:
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


def resolve_match_mode(
    tol: dict,
    match_mode: str = "auto",
    min_criteria_matched: int = None,
) -> tuple:
    """Decide filters.yaml's match_mode / min_criteria_matched -- i.e.
    whether matches_profile() in fetch_tenders_oeffentlichevergabe.py
    requires a tender to satisfy ALL of CPV/region/value, or only SOME of
    them (see that function's docstring for exactly what each mode does).

    match_mode="auto" (the default) derives the setting from how loose the
    cpv/nuts/value tolerance dials already are, using their average:
        avg < 0.35            -> "all"  (strict AND, same as before this
                                  feature existed)
        0.35 <= avg < 0.7      -> "any", min_criteria_matched=2 (need 2 of
                                  the considered core criteria)
        avg >= 0.7             -> "any", min_criteria_matched=1 (any single
                                  considered core criterion is enough)
    These thresholds are a judgment call, not a formula from the ladder
    logic -- tune them here if "auto" ends up too loose or too strict for
    a given run.

    Passing match_mode="all" or "any" explicitly overrides the derivation
    entirely (min_criteria_matched still defaults to 1 if "any" is forced
    without an explicit count). exclude_keywords / role_hint_reject are
    never affected by this -- they stay a hard reject regardless.
    """
    if match_mode not in ("auto", "all", "any"):
        raise ValueError(f"match_mode must be 'auto', 'all', or 'any', got {match_mode!r}")

    if match_mode == "all":
        return "all", None, None
    if match_mode == "any":
        return "any", (min_criteria_matched or 1), None

    avg = (tol["cpv"] + tol["nuts"] + tol["value"]) / 3.0
    if avg < 0.35:
        return "all", None, avg
    elif avg < 0.7:
        return "any", (min_criteria_matched or 2), avg
    else:
        return "any", (min_criteria_matched or 1), avg


def resolve_tolerances(
    tolerance: float = 0.5,
    tolerance_cpv: float = None,
    tolerance_nuts: float = None,
    tolerance_value: float = None,
    tolerance_exclude: float = None,
    tolerance_role_hint: float = None,
) -> dict:
    tol_defaults = {
        "cpv": tolerance_cpv if tolerance_cpv is not None else tolerance,
        "nuts": tolerance_nuts if tolerance_nuts is not None else tolerance,
        "value": tolerance_value if tolerance_value is not None else tolerance,
        "exclude": tolerance_exclude if tolerance_exclude is not None else tolerance,
        "role_hint": tolerance_role_hint if tolerance_role_hint is not None else tolerance,
    }
    for name, val in tol_defaults.items():
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"tolerance for '{name}' must be in [0.0, 1.0], got {val}")
    return tol_defaults


def build_filters_yaml(
    company: dict,
    tol_defaults: dict,
    api_key: str,
    model: str = CLAUDE_MODEL_DEFAULT,
    cache_path: str = ".filter_ladders_cache.json",
    refresh: bool = False,
    match_mode: str = "auto",
    min_criteria_matched: int = None,
) -> str:
    """Core library function: given the already-loaded company dict (the
    single object from company_details.json) and resolved tolerances, call
    Claude (with caching) as needed and return the full rendered
    filters.yaml text. Does not touch --input/--out paths itself."""
    cache = {} if refresh else load_cache(cache_path)

    name = company.get("name", "unnamed")
    cache_key = compute_cache_key(company)

    if cache_key in cache and not refresh:
        print(f"{name}: using cached ladder ({cache_path}, key {cache_key})")
        ladders = cache[cache_key]
    else:
        print(f"{name}: calling Claude ({model}) to build filter ladder (cache key {cache_key})...")
        prompt = build_prompt(company)
        ladders = call_claude(prompt, api_key, model)
        cache[cache_key] = ladders
        save_cache(cache_path, cache)

    validate_ladder(ladders["cpv_ladder"], f"{name} cpv_ladder", allow_empty_at_1_0_only=True)
    validate_ladder(ladders["nuts_ladder"], f"{name} nuts_ladder", allow_empty_at_1_0_only=True)
    validate_ladder(ladders["exclude_keywords_ladder"], f"{name} exclude_keywords_ladder", allow_empty_at_1_0_only=False)
    validate_ladder(ladders["role_hint_ladder"], f"{name} role_hint_ladder", allow_empty_at_1_0_only=False)

    body = render_filters_body(company, ladders, tol_defaults, match_mode, min_criteria_matched)
    print(f"  -> resolved filters.yaml body for '{name}'")

    return render_header(tol_defaults, cache_key) + body + "\n"


def run(
    input_path: str = "company_details.json",
    out_path: str = "filters.yaml",
    model: str = CLAUDE_MODEL_DEFAULT,
    cache_path: str = None,
    refresh: bool = False,
    tolerance: float = 0.5,
    tolerance_cpv: float = None,
    tolerance_nuts: float = None,
    tolerance_value: float = None,
    tolerance_exclude: float = None,
    tolerance_role_hint: float = None,
    api_key: str = None,
    match_mode: str = "auto",
    min_criteria_matched: int = None,
) -> str:
    """Library entry point mirroring the CLI end to end: load
    company_details.json (a single flat company object), resolve
    tolerances, call Claude (cached), write filters.yaml, and return its
    text.

    match_mode / min_criteria_matched control how the written filters.yaml
    combines CPV/region/value (see resolve_match_mode()'s docstring):
    "auto" (default) derives it from how loose the tolerance dials already
    are; "all" or "any" force it explicitly.
    """
    api_key = api_key or get_anthropic_api_key()

    tol_defaults = resolve_tolerances(
        tolerance, tolerance_cpv, tolerance_nuts, tolerance_value,
        tolerance_exclude, tolerance_role_hint,
    )

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"input file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        company = json.load(f)
    if not isinstance(company, dict) or not company:
        raise ValueError(
            f"{input_path} must contain a single company object "
            f"(a flat JSON mapping of company detail fields, not a list)"
        )

    resolved_cache_path = cache_path or os.path.join(
        os.path.dirname(os.path.abspath(out_path)) or ".", ".filter_ladders_cache.json"
    )

    output = build_filters_yaml(
        company, tol_defaults, api_key, model=model,
        cache_path=resolved_cache_path, refresh=refresh,
        match_mode=match_mode, min_criteria_matched=min_criteria_matched,
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\nWrote {out_path} for '{company.get('name', 'company')}'.")
    print(f"Ladder cache: {resolved_cache_path} (re-run with different --tolerance-* flags without re-calling Claude)")
    return output


def main():
    parser = argparse.ArgumentParser(description="Convert company_details.json into filters.yaml via Claude, with a per-criterion tolerance dial.")
    parser.add_argument("--input", default="company_details.json", help="Path to company_details.json (default: company_details.json)")
    parser.add_argument("--out", default="filters.yaml", help="Output filters.yaml path (default: filters.yaml)")
    parser.add_argument("--model", default=CLAUDE_MODEL_DEFAULT, help=f"Claude model (default: {CLAUDE_MODEL_DEFAULT})")
    parser.add_argument("--cache-path", default=None, help="Cache file for the raw Claude ladder (default: .filter_ladders_cache.json next to --out)")
    parser.add_argument("--refresh", action="store_true", help="Ignore cache and re-call Claude")

    parser.add_argument("--tolerance", type=float, default=0.5, help="Global default tolerance in [0,1] for any dial not set explicitly (default: 0.5)")
    parser.add_argument("--tolerance-cpv", type=float, default=None)
    parser.add_argument("--tolerance-nuts", type=float, default=None)
    parser.add_argument("--tolerance-value", type=float, default=None)
    parser.add_argument("--tolerance-exclude", type=float, default=None)
    parser.add_argument("--tolerance-role-hint", type=float, default=None)

    parser.add_argument("--match-mode", choices=["auto", "all", "any"], default="auto",
                         help="How CPV/region/value combine in matches_profile(): 'all' is the "
                              "original strict AND; 'any' lets a tender through if only "
                              "--min-criteria-matched of the three considered criteria hit; "
                              "'auto' (default) derives this from how loose cpv/nuts/value "
                              "tolerance already are (see resolve_match_mode()).")
    parser.add_argument("--min-criteria-matched", type=int, default=None,
                         help="Only used when the resolved match_mode is 'any'. Minimum number "
                              "of the considered core criteria (CPV/region/value) a tender must "
                              "satisfy. Defaults: 'auto' picks 2 or 1 depending on tolerance; "
                              "an explicit --match-mode any with no count given defaults to 1.")
    args = parser.parse_args()

    try:
        api_key = get_anthropic_api_key()
    except RuntimeError as e:
        sys.exit(f"ERROR: {e}")

    try:
        run(
            input_path=args.input,
            out_path=args.out,
            model=args.model,
            cache_path=args.cache_path,
            refresh=args.refresh,
            tolerance=args.tolerance,
            tolerance_cpv=args.tolerance_cpv,
            tolerance_nuts=args.tolerance_nuts,
            tolerance_value=args.tolerance_value,
            tolerance_exclude=args.tolerance_exclude,
            tolerance_role_hint=args.tolerance_role_hint,
            api_key=api_key,
            match_mode=args.match_mode,
            min_criteria_matched=args.min_criteria_matched,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        sys.exit(f"ERROR: {e}")


if __name__ == "__main__":
    main()