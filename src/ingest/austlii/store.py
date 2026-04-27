from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.models.legislation import LegislationRecord


RAW_DIR = Path("data/raw/austlii")
PROCESSED_PATH = Path("data/processed/legislation.jsonl")


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def store_raw_html(jurisdiction: str, source_url: str, html: str) -> Path:
    target_dir = RAW_DIR / jurisdiction
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{_url_hash(source_url)}.html"
    path.write_text(html, encoding="utf-8")
    return path


def append_record(record: LegislationRecord) -> None:
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROCESSED_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record.model_dump(mode="json")) + "\n")


def upsert_record(record: LegislationRecord) -> None:
    """Insert or replace a record by source_id to keep processed dataset idempotent."""
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_processed_rows()

    payload = record.model_dump(mode="json")
    replaced = False

    for i, row in enumerate(existing):
        if str(row.get("source_id")) == record.source_id:
            existing[i] = payload
            replaced = True
            break

    if not replaced:
        existing.append(payload)

    with PROCESSED_PATH.open("w", encoding="utf-8") as f:
        for row in existing:
            f.write(json.dumps(row) + "\n")


def _load_processed_rows() -> list[dict[str, Any]]:
    if not PROCESSED_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in PROCESSED_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows
