"""
One-off inspector: run this locally to see the REAL shape of an OCDS release
from oeffentlichevergabe.de, so we can map region/value/role fields from
ground truth instead of guessing.

Usage:
    python inspect_notice.py                # inspects yesterday's data
    python inspect_notice.py 2026-09-10      # inspects a specific pubDay

It will:
  1. Download that day's OCDS export
  2. Find the first release whose tender.items include a CPV starting with 45
     (construction), since that's the category we care about
  3. Pretty-print the FULL release JSON for that one notice
  4. Print a flattened list of every key path found anywhere in that release,
     so we can see exactly where value/currency/region/address live even if
     they're nested somewhere unexpected.

Paste the output back and we'll wire the real paths into the main script.
"""
import requests
import zipfile
import io
import json
import sys
from datetime import datetime, timedelta

API_URL = "https://oeffentlichevergabe.de/api/notice-exports"


def flatten_keys(obj, prefix=""):
    paths = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            paths.add(p)
            paths |= flatten_keys(v, p)
    elif isinstance(obj, list):
        for item in obj[:1]:  # just look at first element of arrays
            paths |= flatten_keys(item, prefix + "[]")
    return paths


def main():
    pub_day = sys.argv[1] if len(sys.argv) > 1 else (
        datetime.now() - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    print(f"Fetching {pub_day}...")
    resp = requests.get(
        API_URL, params={"pubDay": pub_day, "format": "ocds.zip"}, stream=True
    )
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as archive:
        json_files = [n for n in archive.namelist() if n.endswith(".json")]
        print(f"{len(json_files)} notice files in archive.")

        for fname in json_files:
            with archive.open(fname) as f:
                # Force UTF-8 decoding explicitly (fixes the '?' character issue)
                data = json.loads(f.read().decode("utf-8"))

            for release in data.get("releases", []):
                tender = release.get("tender", {})
                cpvs = [
                    item.get("classification", {}).get("id", "")
                    for item in tender.get("items", [])
                ]
                if any(c.startswith("45") for c in cpvs):
                    print("\n" + "=" * 80)
                    print(f"FOUND sample construction notice in: {fname}")
                    print("=" * 80)
                    print(json.dumps(release, indent=2, ensure_ascii=False))

                    print("\n" + "-" * 80)
                    print("ALL KEY PATHS IN THIS RELEASE:")
                    print("-" * 80)
                    for p in sorted(flatten_keys(release)):
                        print(p)

                    return

        print("No construction-CPV notice found in this day's archive.")


if __name__ == "__main__":
    main()