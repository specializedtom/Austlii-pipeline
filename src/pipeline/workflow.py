from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from src.ingest.austlii.client import AustliiClient
from src.ingest.austlii.discover import discover_seed_urls
from src.ingest.austlii.normalize import normalize_parsed_document
from src.ingest.austlii.parse import parse_html
from src.ingest.austlii.store import append_record, store_raw_html
from src.models.legislation import Jurisdiction

STATE_FILE = Path("data/state/pipeline_state.json")


def ingest(jurisdiction: Jurisdiction) -> int:
    client = AustliiClient()
    count = 0
    for url in discover_seed_urls(jurisdiction):
        html = client.fetch(url)
        store_raw_html(jurisdiction.value, url, html)
        parsed = parse_html(html)
        record = normalize_parsed_document(parsed, url, jurisdiction)
        append_record(record)
        count += 1
    _save_state({"last_ingest_jurisdiction": jurisdiction.value, "records_ingested": count})
    return count


def classify(as_of: date | None = None) -> dict[str, str]:
    # Starter placeholder: full batch re-read/write can be added in next iteration.
    as_of = as_of or date.today()
    sample = {"status": "ok", "as_of": as_of.isoformat()}
    _save_state({"last_classify_as_of": as_of.isoformat()})
    return sample


def _save_state(payload: dict[str, str | int]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        existing = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    else:
        existing = {}
    existing.update(payload)
    STATE_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")
