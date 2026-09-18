"""
backend/workflow_tools/5_select_tendars.py

Reads the standardized tender markdown 4_standardize_tenders.py writes to
backend/standardized_tenders/<company_key>/<notice_id>.md (YAML frontmatter
+ plain-text description body) and picks `count` of them at random,
returning them as plain dicts matching the Tender schema in models.py /
tender-types.ts.

Importable use:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "select_tenders", "5_select_tendars.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tenders = mod.select_tenders(company_key="acme_gmbh", count=3)

(The leading digit means this file can't be imported with a plain
`import 5_select_tendars` statement -- see 1_company_md_to_company_details.py's
docstring for why, and the same importlib pattern applies here.)

Usage:
    python 5_select_tendars.py --company acme_gmbh
    python 5_select_tendars.py --company acme_gmbh --count 3 --seed 42
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DEFAULT_STANDARDIZED_DIR = BACKEND_DIR / "standardized_tenders"
DEFAULT_COUNT = 3

# Matches a leading "---\n...\n---\n" YAML frontmatter block followed by the
# plain-text description body, exactly what render_standardized_markdown()
# in 4_standardize_tenders.py writes.
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def parse_standardized_md(path: Path) -> dict:
    """Parse one standardized tender .md into a Tender-shaped dict (the
    frontmatter fields plus a "description" key holding the body text)."""
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path.name}: no YAML frontmatter block found")

    frontmatter_text, body = match.group(1), match.group(2)
    record = yaml.safe_load(frontmatter_text)
    if not isinstance(record, dict):
        raise ValueError(f"{path.name}: frontmatter did not parse to a mapping")

    record["description"] = body.strip()
    return record


def select_tenders(
    company_key: str,
    count: int = DEFAULT_COUNT,
    standardized_dir: Path = DEFAULT_STANDARDIZED_DIR,
    seed: int = None,
) -> list:
    """Library entry point: read every standardized .md for company_key and
    return up to `count` of them chosen at random, as Tender-shaped dicts.
    Files that fail to parse are skipped (and noted via print()) rather
    than aborting the whole selection.

    Raises FileNotFoundError / ValueError (never sys.exit) so it's safe to
    call from other code, e.g. a web backend.
    """
    standardized_dir = Path(standardized_dir)
    company_dir = standardized_dir / company_key
    if not company_dir.exists():
        raise FileNotFoundError(
            f"no standardized tenders folder for '{company_key}' at {company_dir}"
        )

    md_files = sorted(company_dir.glob("*.md"))
    if not md_files:
        raise ValueError(f"no standardized tender files found in {company_dir}")

    rng = random.Random(seed) if seed is not None else random
    candidates = list(md_files)
    rng.shuffle(candidates)

    tenders = []
    for path in candidates:
        if len(tenders) >= count:
            break
        try:
            tenders.append(parse_standardized_md(path))
        except Exception as e:
            print(f"  SKIP {path.name}: {e}")

    if not tenders:
        raise ValueError(f"found {len(md_files)} file(s) in {company_dir} but none parsed successfully")

    return tenders


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--company", required=True, help="Company key (folder name under standardized_tenders/)")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help=f"How many to pick (default: {DEFAULT_COUNT})")
    parser.add_argument("--standardized-dir", type=Path, default=DEFAULT_STANDARDIZED_DIR)
    parser.add_argument("--seed", type=int, default=None, help="Random seed, for reproducible picks")
    args = parser.parse_args()

    try:
        tenders = select_tenders(
            company_key=args.company,
            count=args.count,
            standardized_dir=args.standardized_dir,
            seed=args.seed,
        )
    except (FileNotFoundError, ValueError) as e:
        sys.exit(f"ERROR: {e}")

    print(json.dumps(tenders, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()