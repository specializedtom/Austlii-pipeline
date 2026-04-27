from __future__ import annotations

from urllib.parse import urlparse

from src.models.legislation import InstrumentType, Jurisdiction, LegislationRecord


def normalize_parsed_document(parsed: dict[str, str], source_url: str, jurisdiction: Jurisdiction) -> LegislationRecord:
    title = parsed.get("title", "Untitled")
    source_id = urlparse(source_url).path.strip("/") or source_url
    return LegislationRecord(
        source_url=source_url,
        source_id=source_id,
        short_title=title,
        full_title=title,
        jurisdiction=jurisdiction,
        instrument_type=InstrumentType.ACT,
        text=parsed.get("text"),
    )
