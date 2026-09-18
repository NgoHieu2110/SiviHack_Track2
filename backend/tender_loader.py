"""
Loads tender/package .md files from disk into `Tender` objects and keeps
an in-memory cache that auto-refreshes when files change.

EXPECTED FILE FORMAT (YAML frontmatter + markdown body):

    ---
    id: "T-2026-014"
    title: "Reconstruction of Provincial Road 42"
    authority: "Department of Transport, Hai Duong Province"
    cpvCode: "45230000"
    cpvLabel: "45230000 — Roads, railways, pipelines, communication lines"
    contractNature: "Works"
    location: "Hai Duong, Vietnam"
    value: 18500000000
    currency: "VND"
    deadline: "2026-11-30"
    role: "Sole contractor"
    requiredCertificates:
      - "ISO 9001 (Quality)"
      - "SOA / Classification Certificate"
    insuranceRequired: 500000000
    guaranteeRequired: "Performance guarantee (5-10%)"
    startDate: "2027-01-15"
    ---
    Free-text description of the project goes here. This becomes the
    `description` field and is also given to Claude as extra context.

If your real .md files use a different structure, tell me and I'll adjust
this parser to match exactly — this is a reasonable default in the
meantime so the pipeline works end to end.

Caching strategy: on every access we `stat()` each .md file; only files
that are new or whose mtime changed get re-parsed. A manual POST
/admin/reload endpoint (see main.py) forces a full reload immediately.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass

import yaml

from models import Tender

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n?(.*)$", re.DOTALL)


@dataclass
class LoadedTender:
    filename: str
    mtime: float
    tender: Tender
    raw_markdown: str  # full original file content, given to Claude as-is


def _parse_md_file(path: str, filename: str) -> LoadedTender:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    match = FRONTMATTER_RE.match(raw)
    if not match:
        raise ValueError(
            f"'{filename}' has no YAML frontmatter (expected a '---' block "
            f"at the top). See tender_loader.py docstring for the format."
        )

    frontmatter_text, body = match.group(1), match.group(2).strip()
    data = yaml.safe_load(frontmatter_text) or {}

    if "description" not in data or not data["description"]:
        data["description"] = body

    # id/title/etc are required by the Tender model; a clear error here is
    # far more useful than a cryptic Pydantic stack trace at request time.
    try:
        tender = Tender(**data)
    except Exception as e:  # noqa: BLE001 - want to add filename context
        raise ValueError(f"'{filename}' failed validation: {e}") from e

    return LoadedTender(
        filename=filename,
        mtime=os.path.getmtime(path),
        tender=tender,
        raw_markdown=raw,
    )


class TenderCache:
    def __init__(self, directory: str):
        self.directory = directory
        self._lock = threading.Lock()
        self._docs: dict[str, LoadedTender] = {}
        self._errors: dict[str, str] = {}  # filename -> last parse error

    def _scan_dir(self) -> dict[str, float]:
        if not os.path.isdir(self.directory):
            return {}
        found = {}
        for name in os.listdir(self.directory):
            if not name.lower().endswith(".md"):
                continue
            full_path = os.path.join(self.directory, name)
            if os.path.isfile(full_path):
                found[name] = os.path.getmtime(full_path)
        return found

    def get_all(self, force_reload: bool = False) -> list[LoadedTender]:
        """Return current tenders, refreshing any new/changed/removed files."""
        with self._lock:
            on_disk = self._scan_dir()

            for filename in list(self._docs.keys()):
                if filename not in on_disk:
                    del self._docs[filename]
            for filename in list(self._errors.keys()):
                if filename not in on_disk:
                    del self._errors[filename]

            for filename, mtime in on_disk.items():
                cached = self._docs.get(filename)
                needs_reload = (
                    force_reload or cached is None or cached.mtime != mtime
                )
                if needs_reload:
                    full_path = os.path.join(self.directory, filename)
                    try:
                        self._docs[filename] = _parse_md_file(full_path, filename)
                        self._errors.pop(filename, None)
                    except Exception as e:  # noqa: BLE001
                        # Don't let one bad file take down the whole endpoint.
                        self._errors[filename] = str(e)
                        self._docs.pop(filename, None)

            return list(self._docs.values())

    def reload(self) -> dict:
        docs = self.get_all(force_reload=True)
        return {"loaded": len(docs), "errors": dict(self._errors)}

    def get_errors(self) -> dict[str, str]:
        return dict(self._errors)
