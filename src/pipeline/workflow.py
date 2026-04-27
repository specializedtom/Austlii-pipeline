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
FAILED_FILE = Path("data/state/failed_urls.jsonl")


def ingest(jurisdiction: Jurisdiction, fail_fast: bool = False) -> dict[str, int | str]:
    client = AustliiClient()
    count = 0
    failures = 0
    for url in discover_seed_urls(jurisdiction):
        try:
            html = client.fetch(url)
            store_raw_html(jurisdiction.value, url, html)
            parsed = parse_html(html)
            record = normalize_parsed_document(parsed, url, jurisdiction)
            append_record(record)
            count += 1
        except Exception as exc:  # noqa: BLE001
            failures += 1
            _append_failed_url(jurisdiction.value, url, str(exc))
            if fail_fast:
                raise

    result = {
        "jurisdiction": jurisdiction.value,
        "records_ingested": count,
        "records_failed": failures,
    }
    _save_state(result)
    return result


def classify(as_of: date | None = None) -> dict[str, str]:
    as_of = as_of or date.today()
    sample = {"status": "ok", "as_of": as_of.isoformat()}
    _save_state({"last_classify_as_of": as_of.isoformat()})
    return sample


def _append_failed_url(jurisdiction: str, url: str, error: str) -> None:
    FAILED_FILE.parent.mkdir(parents=True, exist_ok=True)
    row = {"jurisdiction": jurisdiction, "url": url, "error": error}
    with FAILED_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def _save_state(payload: dict[str, str | int]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        existing = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    else:
        existing = {}
    existing.update(payload)
    STATE_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")
