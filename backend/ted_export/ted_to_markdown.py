#!/usr/bin/env python3
"""
ted_to_markdown.py

Pulls procurement notices from the official TED (Tenders Electronic Daily)
Search API v3 and writes each notice out as a Markdown file, including the
notice's full published text (not just index metadata).

Docs:  https://docs.ted.europa.eu/api/latest/search.html
Query builder / field reference: https://ted.europa.eu/en/search/expert-search
Search endpoint: POST https://api.ted.europa.eu/v3/notices/search  (no API key)
Notice page:      GET  https://ted.europa.eu/en/notice/{publication-number}/html

USAGE EXAMPLES
---------------
python ted_to_markdown.py --query 'place-of-performance IN (DEU)' --max 100

python ted_to_markdown.py \
    --query 'FT ~ "solar panels" AND publication-date >= 2026-01-01' \
    --max 200 --outdir ted_export

# Metadata only, skip fetching the full notice text (much faster)
python ted_to_markdown.py --query 'place-of-performance IN (DEU)' --max 100 --no-fulltext

Build/test your expert-search query string at:
https://ted.europa.eu/en/search/expert-search
then paste it into --query.
"""

import argparse
import re
import sys
import time
from html import unescape
from pathlib import Path

import requests

SEARCH_API_URL = "https://api.ted.europa.eu/v3/notices/search"
NOTICE_HTML_URL = "https://ted.europa.eu/en/notice/{pub}/html"

# Metadata fields to request from the Search API index.
# TED has 1800+ possible field names (eForms kebab-case names), and not every
# one applies to every notice/scope -- an unsupported name makes the WHOLE
# request fail with HTTP 400. This is a conservative, confirmed-working set.
# To find more/other valid names for your use case, build a query on
# https://ted.europa.eu/en/search/expert-search (it lists all field names)
# and copy the ones you need into --fields.
DEFAULT_FIELDS = [
    "publication-number",
    "notice-title",
    "notice-type",
    "contract-nature",
    "buyer-name",
    "buyer-country",
    "classification-cpv",
    "total-value",
    "total-value-cur",
    "publication-date",
    "deadline",
    "links",
]

# Minimal fallback used if a request still comes back as 400 (e.g. because a
# custom --fields list included an unsupported name for this notice scope).
SAFE_FALLBACK_FIELDS = ["publication-number", "notice-title", "links"]


def slugify(text: str, maxlen: int = 60) -> str:
    text = re.sub(r"[^\w\-]+", "-", text.strip().lower())
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:maxlen] or "notice"


def flatten(value):
    """TED metadata fields are often lists, language-keyed dicts, or scalars."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(flatten(v) for v in value if v not in (None, ""))
    if isinstance(value, dict):
        if "eng" in value:
            return flatten(value["eng"])
        return "; ".join(flatten(v) for v in value.values())
    return str(value)


def pick_link(links_value, category: str):
    """links_value is a dict like {'html': {'ENG': 'url', 'FRA': 'url', ...}, 'pdf': {...}, 'xml': {...}}.
    Return one representative URL (prefer English) for the given category."""
    if not isinstance(links_value, dict):
        return None
    section = links_value.get(category)
    if not section:
        return None
    if isinstance(section, str):
        return section
    if isinstance(section, list):
        return section[0] if section else None
    if isinstance(section, dict):
        for lang_key in ("ENG", "eng", "EN", "en"):
            if lang_key in section:
                return section[lang_key]
        return next(iter(section.values()), None)
    return None


def fetch_notices(query: str, fields: list, max_notices: int, page_size: int = 100):
    """Iterate through all matching notices using TED's ITERATION pagination mode."""
    collected = []
    token = None
    session = requests.Session()

    while len(collected) < max_notices:
        body = {
            "query": query,
            "fields": fields,
            "limit": min(page_size, max_notices - len(collected)),
            "scope": "ACTIVE",
            "checkQuerySyntax": False,
            "paginationMode": "ITERATION",
        }
        if token:
            body["iterationNextToken"] = token

        resp = session.post(SEARCH_API_URL, json=body, headers={"Accept": "application/json"})
        if resp.status_code == 400 and fields != SAFE_FALLBACK_FIELDS:
            print(
                "  Got HTTP 400 (likely an unsupported field name). "
                f"Retrying this page with a minimal safe field set: {SAFE_FALLBACK_FIELDS}\n"
                "  For the exact list of valid field names for your query, check "
                "https://ted.europa.eu/en/search/expert-search",
                file=sys.stderr,
            )
            fields = SAFE_FALLBACK_FIELDS
            body["fields"] = fields
            resp = session.post(SEARCH_API_URL, json=body, headers={"Accept": "application/json"})
        if resp.status_code != 200:
            print(f"API error {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
            resp.raise_for_status()

        data = resp.json()
        notices = data.get("notices", [])
        if not notices:
            break

        collected.extend(notices)
        print(f"  fetched {len(collected)} notices so far...")

        token = data.get("iterationNextToken")
        if not token:
            break
        time.sleep(0.2)  # be polite to the API

    return collected[:max_notices]


_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_ANY_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")
_BLANKLINES_RE = re.compile(r"\n{3,}")


def html_to_text(html: str) -> str:
    """Very lightweight HTML -> plain text conversion (no extra dependencies)."""
    html = _TAG_RE.sub(" ", html)
    html = re.sub(r"(?i)</(p|div|tr|li|h[1-6])>", "\n", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    text = _ANY_TAG_RE.sub("", html)
    text = unescape(text)
    text = _WS_RE.sub(" ", text)
    lines = [ln.strip() for ln in text.splitlines()]
    text = "\n".join(ln for ln in lines if ln)
    text = _BLANKLINES_RE.sub("\n\n", text)
    return text.strip()


def fetch_fulltext(pub_number: str, session: requests.Session) -> str:
    """Download the notice's own public HTML page and extract its text.
    This is where the actual published content (scope of work, criteria,
    conditions, etc.) lives -- the search index only has structured
    metadata, which is often sparse for older, pre-eForms notices."""
    url = NOTICE_HTML_URL.format(pub=pub_number)
    try:
        resp = session.get(url, timeout=30, headers={"Accept": "text/html"})
        resp.raise_for_status()
        
        # --- THÊM DÒNG NÀY ĐỂ ÉP NHẬN DIỆN ĐÚNG BẢNG MÃ UTF-8 ---
        resp.encoding = resp.apparent_encoding
        
    except requests.RequestException as e:
        return f"(could not fetch full text: {e})"
    
    # Keep just the main content area if we can find it, else the whole body.
    body_match = re.search(r"(?is)<main.*?</main>", resp.text)
    html = body_match.group(0) if body_match else resp.text
    return html_to_text(html)


def notice_to_markdown(notice: dict, fulltext: str = None) -> str:
    pub_number = flatten(notice.get("publication-number", "unknown"))
    title = flatten(notice.get("notice-title")) or "(no title)"

    lines = [f"# {title}", ""]
    lines.append(f"**Publication number:** {pub_number}")

    links_value = notice.get("links")

    for key, value in notice.items():
        if key in ("publication-number", "notice-title", "links"):
            continue
        text = flatten(value)
        if not text:
            continue
        label = key.replace("-", " ").capitalize()
        lines.append(f"**{label}:** {text}")

    html_link = pick_link(links_value, "html") or (
        f"https://ted.europa.eu/en/notice/{pub_number}/html" if pub_number != "unknown" else None
    )
    pdf_link = pick_link(links_value, "pdf")

    if html_link or pdf_link:
        lines.append("")
        if html_link:
            lines.append(f"[View on TED (HTML)]({html_link})")
        if pdf_link:
            lines.append(f"[View on TED (PDF)]({pdf_link})")

    if fulltext:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Full notice text")
        lines.append("")
        lines.append(fulltext)

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Export TED notices to Markdown files.")
    parser.add_argument("--query", required=True, help="TED expert-search query string")
    parser.add_argument("--fields", nargs="+", default=DEFAULT_FIELDS, help="Metadata fields to retrieve")
    parser.add_argument("--max", type=int, default=100, help="Max notices to fetch (default 100)")
    parser.add_argument("--outdir", default="ted_export", help="Output directory")
    parser.add_argument(
        "--no-fulltext",
        action="store_true",
        help="Skip fetching each notice's full published text (faster, metadata only)",
    )
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # --- THÊM ĐOẠN NÀY ĐỂ XÓA CÁC FILE .MD CŨ TRƯỚC KHI TẢI MỚI ---
    for old_file in outdir.glob("*.md"):
        try:
            old_file.unlink()
        except Exception as e:
            print(f"Không thể xóa file cũ {old_file}: {e}", file=sys.stderr)
    # -------------------------------------------------------------

    print(f"Querying TED Search API: {args.query!r}")
    notices = fetch_notices(args.query, args.fields, args.max)
    print(f"Retrieved {len(notices)} notices.")

    session = requests.Session()
    index_lines = [
        "# TED Notices Export",
        "",
        f"Query: `{args.query}`",
        "",
        "| # | Title | Publication number |",
        "|---|---|---|",
    ]

    for i, notice in enumerate(notices, start=1):
        pub_number = flatten(notice.get("publication-number", f"notice-{i}"))
        title = flatten(notice.get("notice-title")) or "(no title)"
        print(f"  [{i}/{len(notices)}] {pub_number} - {title[:60]}")

        fulltext = None
        if not args.no_fulltext and pub_number != "unknown":
            fulltext = fetch_fulltext(pub_number, session)
            time.sleep(0.2)  # be polite to the site

        filename = f"{slugify(pub_number)}.md"
        (outdir / filename).write_text(notice_to_markdown(notice, fulltext), encoding="utf-8")
        index_lines.append(f"| {i} | {title[:80]} | [{pub_number}]({filename}) |")

    (outdir / "_index.md").write_text("\n".join(index_lines), encoding="utf-8")
    print(f"Done. Wrote {len(notices)} notice files + _index.md to {outdir}/")


if __name__ == "__main__":
    main()