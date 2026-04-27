from __future__ import annotations

import hashlib
import json
from pathlib import Path

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
