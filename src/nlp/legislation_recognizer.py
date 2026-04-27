from __future__ import annotations

import re
from collections.abc import Iterable

from src.models.legislation import LegislationRecord, RecognitionResult, ResolvedMention

CITATION_PATTERN = re.compile(r"\b([A-Z][A-Za-z\s]+\sAct\s\d{4})\b")


def extract_mentions(text: str) -> list[str]:
    return [m.group(1).strip() for m in CITATION_PATTERN.finditer(text)]


def resolve_mentions(input_id: str, text: str, corpus: Iterable[LegislationRecord]) -> RecognitionResult:
    mentions = extract_mentions(text)
    by_title = {r.short_title.lower(): r for r in corpus}

    result = RecognitionResult(input_id=input_id)
    for mention in mentions:
        key = mention.lower()
        match = by_title.get(key)
        if match:
            result.matched_instruments.append(
                ResolvedMention(
                    mention=mention,
                    matched_source_id=match.source_id,
                    confidence=0.95,
                )
            )
        else:
            result.unresolved_mentions.append(mention)
    return result
