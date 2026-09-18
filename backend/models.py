"""
Pydantic models mirroring ./tender-types.ts exactly.

CompanyProfile  -> sent by the frontend as the POST body.
Tender          -> one procurement package, built from a standardized .md
                   file (see 4_standardize_tenders.py / 5_select_tendars.py).
TenderMatch     -> { tender, score, reasons, considerations, summary }
                   this is what we return as `{ matches: TenderMatch[] }`.

NOTE ON OPTIONAL FIELDS: 4_standardize_tenders.py explicitly leaves role,
requiredCertificates, insuranceRequired, guaranteeRequired, startDate (and,
less often, value/currency/location/deadline/cpvCode/cpvLabel/contractNature)
as null when the source OCDS notice doesn't carry a reliable equivalent --
see that script's docstring. Tender below mirrors that reality (Optional
with sensible defaults) rather than pretending every field is always
populated.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CompanyProfile(BaseModel):
    model_config = ConfigDict(extra="allow")
    does: str
    placeOfPerformance: str
    contractValueMin: str
    contractValueMax: str
    exclusions: str = ""
    specifications: str = ""
    revenue: float
    employees: int


class Tender(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str | None = None
    authority: str | None = None
    cpvCode: str | None = None
    cpvLabel: str | None = None
    contractNature: str | None = None
    location: str | None = None
    value: float | None = None
    currency: str | None = None
    deadline: str | None = None
    role: str | None = None
    requiredCertificates: list[str] = Field(default_factory=list)
    insuranceRequired: float | None = None
    guaranteeRequired: str | None = None
    startDate: str | None = None
    description: str = ""


class TenderMatch(BaseModel):
    model_config = ConfigDict(extra="allow")

    tender: Tender
    score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    considerations: list[str] = Field(default_factory=list)
    summary: str = ""


class MatchTendersResponse(BaseModel):
    matches: list[TenderMatch]