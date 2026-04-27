from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_PROCESSED_PATH = Path("data/processed/legislation.jsonl")
STRUCTURE_RE = re.compile(r"\b(?:division|div\.?|section|sec\.?|clause|cl\.?|part)\s+[A-Za-z0-9.-]+\b", re.IGNORECASE)


def load_records(path: Path = DEFAULT_PROCESSED_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _extract_snippets(text: str, query: str, max_snippets: int = 3) -> list[str]:
    if not text.strip():
        return []

    q = query.lower().strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    snippets: list[str] = []

    for line in lines:
        lower = line.lower()
        if q in lower or STRUCTURE_RE.search(lower):
            snippets.append(line[:240])
        if len(snippets) >= max_snippets:
            break

    return snippets


def search_records(
    query: str,
    records: list[dict[str, Any]],
    jurisdiction: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    q = query.strip().lower()

    def matches(record: dict[str, Any]) -> bool:
        if jurisdiction and str(record.get("jurisdiction", "")).lower() != jurisdiction.lower():
            return False
        if status and str(record.get("status", "")).lower() != status.lower():
            return False

        haystacks = [
            str(record.get("short_title", "")),
            str(record.get("full_title", "")),
            str(record.get("source_id", "")),
            str(record.get("normalized_citation", "")),
            str(record.get("text", "")),
        ]
        return any(q in h.lower() for h in haystacks)

    filtered = [r for r in records if matches(r)]
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in filtered:
        key = str(row.get("source_id") or row.get("source_url") or "")
        if key and key in seen:
            continue
        if key:
            seen.add(key)

        enriched = dict(row)
        enriched["snippets"] = _extract_snippets(str(row.get("text", "")), query)
        deduped.append(enriched)
    return deduped[:limit]
