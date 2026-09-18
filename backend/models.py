"""
Pydantic models mirroring ./tender-types.ts exactly.

CompanyProfile  -> sent by the frontend as the POST body.
Tender          -> one procurement package, built from a parsed .md file.
TenderMatch     -> { tender, score, reasons, considerations, summary }
                   this is what we return as `{ matches: TenderMatch[] }`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CompanyProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    does: str
    contractNature: str
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
    title: str
    authority: str
    cpvCode: str
    cpvLabel: str
    contractNature: str
    location: str
    value: float
    currency: str
    deadline: str
    role: str
    requiredCertificates: list[str] = Field(default_factory=list)
    insuranceRequired: float = 0
    guaranteeRequired: str = ""
    startDate: str = ""
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