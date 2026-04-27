from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Jurisdiction(str, Enum):
    CTH = "Cth"
    NSW = "NSW"
    VIC = "VIC"
    QLD = "QLD"
    WA = "WA"
    SA = "SA"
    TAS = "TAS"
    ACT = "ACT"
    NT = "NT"


class InstrumentType(str, Enum):
    ACT = "Act"
    REGULATION = "Regulation"
    RULE = "Rule"
    BYLAW = "ByLaw"
    ORDER = "Order"


class LegislationStatus(str, Enum):
    OPERATIVE = "operative"
    REPEALED = "repealed"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


class LegislationRecord(BaseModel):
    source_url: HttpUrl
    source_id: str = Field(description="AustLII source identifier")
    short_title: str
    full_title: str
    year: Optional[int] = None
    instrument_number: Optional[str] = None
    jurisdiction: Jurisdiction
    instrument_type: InstrumentType
    status: LegislationStatus = LegislationStatus.UNKNOWN
    in_force_start: Optional[date] = None
    in_force_end: Optional[date] = None
    amendment_history_ref: Optional[str] = None
    normalized_citation: Optional[str] = None
    text: Optional[str] = None

    @field_validator("short_title", "full_title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return " ".join(value.split()).strip()


class ResolvedMention(BaseModel):
    mention: str
    matched_source_id: str
    confidence: float


class RecognitionResult(BaseModel):
    input_id: str
    matched_instruments: list[ResolvedMention] = Field(default_factory=list)
    unresolved_mentions: list[str] = Field(default_factory=list)
    rationale: Optional[str] = None
