#!/usr/bin/env python3
"""
backend/workflow_tools/1_company_md_to_company_details.py

Converts a freeform Markdown company profile (e.g. company.md) into a
structured JSON record matching the schema used in company_details.json,
using the Gemini API to do the extraction.

Importable use:
    from importlib import import_module
    mod = import_module("1_company_md_to_company_details")  # see note below
    record = mod.company_md_to_details("path/to/company.md")

    # or, appending straight into company_details.json like the CLI does:
    data = mod.run(["path/to/company.md"], out_path="company_details.json")

Note on the leading digit: this file can't be imported with a normal
`import 1_company_md_to_company_details` statement (Python identifiers
can't start with a digit). Either use importlib as above, or from a
sibling script in the same folder do:

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "company_md_to_details", "1_company_md_to_company_details.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

CLI usage (unchanged):
    export GEMINI_API_KEY="your-key-here"   # or set it in backend/.env
    python 1_company_md_to_company_details.py path/to/company.md \
        [--out company_details.json] [--model gemini-2.5-flash]

Behavior:
    - Reads the markdown file.
    - Sends it to Gemini with a prompt describing the exact target schema
      (mirroring the fields seen in company_details.json: name, description,
      Revenue, Employees, founded, contractNature, does, placeOfPerformance,
      contractValueMin, contractValueMax, exclusions, specifications).
    - Parses Gemini's JSON response.
    - If --out already exists and contains {"companies": [...]}, the new
      company record is appended to that list. Otherwise a new file is
      created with that structure.

Security note:
    The Gemini API key is read from the GEMINI_API_KEY environment variable
    (loading backend/.env automatically if it's not already set -- see
    common.py). Never hardcode API keys in source files or commit them to
    version control. If a key has ever been pasted into a chat, a document,
    or a public repo, treat it as compromised and rotate it immediately in
    Google AI Studio.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

from common import get_gemini_api_key

GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"
GEMINI_ENDPOINT_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

SCHEMA_DESCRIPTION = """
Extract information from the markdown company profile below and return ONLY
a single JSON object (no markdown fences, no commentary) with exactly these
fields:

{
  "name": string,                  // company legal name
  "description": string,           // a short 2-5 word tag, e.g. "the regional civil contractor"
  "Revenue": number,                // annual revenue in EUR, integer, no currency symbols
  "Employees": number,              // integer headcount
  "founded": number,                 // year founded, integer
  "contractNature": string,         // same short tag as description, kept consistent with it
  "does": string,                   // 1-3 sentences describing what the company does
  "placeOfPerformance": string,     // geographic area / region they operate in, including any radius/travel constraints
  "contractValueMin": number,       // smallest contract value they'd realistically take, integer EUR
  "contractValueMax": number,       // largest contract value they could handle, integer EUR
  "exclusions": string,             // what they cannot or will not do, plus any direct quotes from the company about limitations
  "specifications": string          // other constraints: financial/bonding limits, capacity limits, reference projects, direct quotes
}

Rules:
- If a value is not stated or cannot be reasonably inferred, use null for
  numbers or an empty string for text — do not invent numbers.
- Keep any direct quotes from the source text intact and attribute them
  naturally within "exclusions" or "specifications", matching the style
  of quoting the company's own words in single quotes.
- Numbers must be plain JSON numbers (no "€", no commas, no "M"/"k" suffixes).
- Return raw JSON only.
"""


def read_markdown(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def call_gemini(markdown_text: str, api_key: str, model: str) -> dict:
    url = GEMINI_ENDPOINT_TEMPLATE.format(model=model)
    prompt = SCHEMA_DESCRIPTION + "\n\n--- MARKDOWN PROFILE START ---\n" + markdown_text + "\n--- MARKDOWN PROFILE END ---\n"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {e.code}: {err_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not reach Gemini API: {e}") from e

    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini response shape: {json.dumps(body)[:500]}") from e

    # Strip accidental markdown fences, just in case.
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Could not parse JSON from Gemini output:\n{cleaned}") from e


def load_existing(out_path: str) -> dict:
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        if "companies" not in data or not isinstance(data["companies"], list):
            data["companies"] = []
        return data
    return {"companies": []}


def company_md_to_details(
    markdown_path: str,
    api_key: str = None,
    model: str = GEMINI_MODEL_DEFAULT,
) -> dict:
    """Core library function: read one markdown profile, call Gemini, return
    the extracted company record as a dict (does NOT write/append to any
    output file -- that's what `run()` does). Raises FileNotFoundError /
    RuntimeError on failure instead of calling sys.exit, so it's safe to
    call from other code."""
    if not os.path.exists(markdown_path):
        raise FileNotFoundError(f"markdown file not found: {markdown_path}")

    api_key = api_key or get_gemini_api_key()
    markdown_text = read_markdown(markdown_path)
    return call_gemini(markdown_text, api_key, model)


def run(
    markdown_paths,
    out_path: str = "company_details.json",
    api_key: str = None,
    model: str = GEMINI_MODEL_DEFAULT,
) -> dict:
    """Library entry point mirroring the CLI: extract one or more markdown
    profiles and append each to out_path's {"companies": [...]} list,
    writing the result back to disk. Returns the final combined dict.

    markdown_paths may be a single path (str) or an iterable of paths.
    """
    if isinstance(markdown_paths, (str, os.PathLike)):
        markdown_paths = [markdown_paths]

    api_key = api_key or get_gemini_api_key()
    data = load_existing(out_path)

    for markdown_path in markdown_paths:
        print(f"Sending {markdown_path} to Gemini ({model}) for extraction...")
        company_record = company_md_to_details(markdown_path, api_key=api_key, model=model)
        data["companies"].append(company_record)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Wrote/updated {out_path} (now {len(data['companies'])} companies).")
    return data


def main():
    parser = argparse.ArgumentParser(description="Convert a company markdown profile into company_details.json format via Gemini.")
    parser.add_argument("markdown_path", help="Path to the input markdown file (e.g. company.md)")
    parser.add_argument("--out", default="company_details.json", help="Output JSON file (default: company_details.json)")
    parser.add_argument("--model", default=GEMINI_MODEL_DEFAULT, help=f"Gemini model to use (default: {GEMINI_MODEL_DEFAULT})")
    args = parser.parse_args()

    try:
        api_key = get_gemini_api_key()
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.markdown_path):
        print(f"ERROR: markdown file not found: {args.markdown_path}", file=sys.stderr)
        sys.exit(1)

    try:
        run([args.markdown_path], out_path=args.out, api_key=api_key, model=args.model)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()