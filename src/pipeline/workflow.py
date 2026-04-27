from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from src.classify.operative_status import classify_operative_status
from src.ingest.austlii.client import AustliiClient
from src.ingest.austlii.discover import discover_legislation_urls
from src.ingest.austlii.normalize import normalize_parsed_document
from src.ingest.austlii.parse import parse_html
from src.ingest.austlii.store import store_raw_html, upsert_record
from src.models.legislation import LegislationRecord, LegislationStatus, Jurisdiction
from src.pipeline.search import _extract_snippets

STATE_FILE = Path("data/state/pipeline_state.json")
FAILED_FILE = Path("data/state/failed_urls.jsonl")
PROCESSED_FILE = Path("data/processed/legislation.jsonl")


def ingest(
    jurisdiction: Jurisdiction,
    fail_fast: bool = False,
    max_docs: int = 100,
) -> dict[str, int | str]:
    client = AustliiClient()
    count = 0
    failures = 0

    try:
        targets = discover_legislation_urls(jurisdiction, client=client, max_docs=max_docs)
    except Exception as exc:  # noqa: BLE001
        targets = []
        failures += 1
        _append_failed_url(jurisdiction.value, "<seed_discovery>", str(exc))
        if fail_fast:
            raise

    for url in targets:
        try:
            html = client.fetch(url)
            store_raw_html(jurisdiction.value, url, html)
            parsed = parse_html(html)
            record = normalize_parsed_document(parsed, url, jurisdiction)
            upsert_record(record)
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
        "targets_discovered": len(targets),
    }
    _save_state(result)
    return result


def query_live(
    query: str,
    jurisdiction: Jurisdiction,
    status: str | None = None,
    max_docs: int = 100,
    as_of: date | None = None,
) -> list[dict[str, str]]:
    """Query AustLII directly without reading/writing local processed cache."""
    as_of = as_of or date.today()
    client = AustliiClient()
    targets = discover_legislation_urls(jurisdiction, client=client, max_docs=max_docs)

    q = query.strip().lower()
    seen: set[str] = set()
    matches: list[dict[str, str]] = []

    for url in targets:
        try:
            html = client.fetch(url)
            parsed = parse_html(html)
            record = normalize_parsed_document(parsed, url, jurisdiction)
            classified = classify_operative_status(record, as_of=as_of)

            if status and classified.status.value.lower() != status.lower():
                continue

            haystacks = [classified.short_title, classified.full_title, classified.source_id, classified.normalized_citation or "", classified.text or ""]
            if not any(q in (h or "").lower() for h in haystacks):
                continue

            if classified.source_id in seen:
                continue
            seen.add(classified.source_id)

            matches.append(
                {
                    "title": classified.short_title,
                    "jurisdiction": classified.jurisdiction.value,
                    "status": classified.status.value,
                    "source_id": classified.source_id,
                    "source_url": str(classified.source_url),
                    "snippets": _extract_snippets(classified.text or "", query),
                }
            )
        except Exception as exc:  # noqa: BLE001
            _append_failed_url(jurisdiction.value, url, str(exc))

    return matches


def classify(as_of: date | None = None) -> dict[str, str | int]:
    as_of = as_of or date.today()

    if not PROCESSED_FILE.exists():
        result = {"status": "no_data", "as_of": as_of.isoformat(), "records_classified": 0}
        _save_state({"last_classify_as_of": as_of.isoformat(), "records_classified": 0})
        return result

    rows = [line.strip() for line in PROCESSED_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]

    classified_rows: list[str] = []
    operative_count = 0
    unknown_count = 0
    error_count = 0

    for raw in rows:
        try:
            record = LegislationRecord.model_validate_json(raw)
            updated = classify_operative_status(record, as_of=as_of)
            if updated.status == LegislationStatus.OPERATIVE:
                operative_count += 1
            if updated.status == LegislationStatus.UNKNOWN:
                unknown_count += 1
            classified_rows.append(json.dumps(updated.model_dump(mode="json")))
        except Exception as exc:  # noqa: BLE001
            error_count += 1
            classified_rows.append(raw)
            _append_failed_url("<classification>", "<processed_row>", str(exc))

    PROCESSED_FILE.write_text("\n".join(classified_rows) + ("\n" if classified_rows else ""), encoding="utf-8")

    result = {
        "status": "ok",
        "as_of": as_of.isoformat(),
        "records_classified": len(rows),
        "operative_records": operative_count,
        "unknown_records": unknown_count,
        "classification_errors": error_count,
    }
    _save_state({"last_classify_as_of": as_of.isoformat(), "records_classified": len(rows)})
    return result


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
