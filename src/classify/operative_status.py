from __future__ import annotations

from datetime import date

from src.models.legislation import LegislationRecord, LegislationStatus


REPEAL_MARKERS = ("repealed", "ceased", "superseded")
OPERATIVE_MARKERS = ("in force", "operative", "commenced")


def classify_operative_status(record: LegislationRecord, as_of: date | None = None) -> LegislationRecord:
    as_of = as_of or date.today()
    text = (record.text or "").lower()

    if any(marker in text for marker in REPEAL_MARKERS):
        record.status = LegislationStatus.REPEALED
    elif any(marker in text for marker in OPERATIVE_MARKERS):
        record.status = LegislationStatus.OPERATIVE

    if record.in_force_end and record.in_force_end < as_of:
        record.status = LegislationStatus.REPEALED

    if record.in_force_start and record.in_force_start > as_of:
        record.status = LegislationStatus.UNKNOWN

    return record
