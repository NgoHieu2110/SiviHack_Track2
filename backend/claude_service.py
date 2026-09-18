"""
Calls Claude to score/match tenders against a company profile.

Design choice: we ask Claude to return ONLY {id, score, reasons,
considerations, summary} per tender — never the full Tender object. We
then look up the real Tender from our own cache by id and assemble the
final TenderMatch ourselves. This avoids the model hallucinating or
subtly altering structured fields (value, deadline, certificates, etc.)
that must stay exactly what's on disk.
"""

from __future__ import annotations

import json
import os
import re

import anthropic

from models import CompanyProfile, Tender, TenderMatch
from tender_loader import LoadedTender

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to your .env file."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _build_prompt(profile: CompanyProfile, tenders: list[LoadedTender]) -> str:
    tender_blocks = []
    for doc in tenders:
        t = doc.tender
        tender_blocks.append(
            f"""---
id: {t.id}
title: {t.title}
authority: {t.authority}
cpvCode: {t.cpvCode} ({t.cpvLabel})
contractNature: {t.contractNature}
location: {t.location}
value: {t.value} {t.currency}
deadline: {t.deadline}
role: {t.role}
requiredCertificates: {", ".join(t.requiredCertificates) or "none"}
insuranceRequired: {t.insuranceRequired} {t.currency}
guaranteeRequired: {t.guaranteeRequired}
startDate: {t.startDate}
description: {t.description}
---"""
        )

    return f"""You are a procurement analyst. Compare a company's profile
against a list of tender packages and score how well the company fits
each tender.

COMPANY PROFILE:
- does (company's line of work / scope of activity): {profile.does}
- contractNature the company works in: {profile.contractNature}
- placeOfPerformance (where the company can operate): {profile.placeOfPerformance}
- target contract value range: {profile.contractValueMin} to {profile.contractValueMax}
- specifications (technical capabilities/equipment/methods): {profile.specifications or "none stated"}
- exclusions (things the company cannot/will not do): {profile.exclusions or "none"}
- annual revenue: {profile.revenue}
- number of employees: {profile.employees}

TENDERS ({len(tenders)} total):
{chr(10).join(tender_blocks)}

For EACH tender above, evaluate fit considering:
1. Scope match: does the company's line of work ("does") align with the
   tender's cpvCode/cpvLabel/description
2. Contract nature alignment (Works/Services/Supplies/Mixed)
3. Location match (placeOfPerformance vs tender location)
4. Whether the tender value falls within the company's target value range
5. Technical fit: do the company's specifications match what the tender
   description/requirements call for
6. Financial/operational capacity: is the company's revenue and employee
   count plausible for a contract of this value, insurance requirement,
   and guarantee requirement (flag as a consideration if it looks like a
   stretch, since the profile doesn't state actual insurance/guarantee/
   certificate coverage — note required certificates as an open item to
   verify rather than assuming the company has or lacks them)
7. Any exclusions that would disqualify the company from this tender

Return ONLY a JSON array (no markdown fences, no commentary), one object
per tender, in this exact shape:

[
  {{
    "id": "<tender id, copied exactly>",
    "score": <integer 0-100, overall fit>,
    "reasons": ["short bullet reasons this is a good fit", "..."],
    "considerations": ["short bullet caveats/risks/gaps to watch for", "..."],
    "summary": "one or two sentence plain-language summary of the fit"
  }}
]

Include every tender id exactly once. Be honest about poor fits (low
score) rather than inflating scores."""


def _extract_json_array(text: str) -> list[dict]:
    """Strip markdown code fences if present and parse the JSON array."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


def match_tenders_with_claude(
    profile: CompanyProfile, tenders: list[LoadedTender]
) -> list[TenderMatch]:
    if not tenders:
        return []

    client = _get_client()
    prompt = _build_prompt(profile, tenders)

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude call failed while matching tenders: {e}") from e

    text = "".join(block.text for block in response.content if block.type == "text")
    if not text:
        raise RuntimeError("Claude returned an empty response.")

    try:
        raw_results = _extract_json_array(text)
    except (json.JSONDecodeError, TypeError) as e:
        raise RuntimeError(f"Could not parse Claude's response as JSON: {e}") from e

    tenders_by_id: dict[str, Tender] = {doc.tender.id: doc.tender for doc in tenders}
    matches: list[TenderMatch] = []

    for item in raw_results:
        tender_id = item.get("id")
        tender = tenders_by_id.get(tender_id)
        if tender is None:
            # Claude referenced an id we don't recognize — skip it rather
            # than fail the whole request.
            continue
        matches.append(
            TenderMatch(
                tender=tender,
                score=max(0, min(100, int(item.get("score", 0)))),
                reasons=item.get("reasons", []),
                considerations=item.get("considerations", []),
                summary=item.get("summary", ""),
            )
        )

    matches.sort(key=lambda m: m.score, reverse=True)
    return matches
