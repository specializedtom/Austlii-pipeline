# AustLII Pipeline (Starter Scaffold)

This repository contains a starter Python pipeline for:

1. Ingesting legislation content from AustLII.
2. Normalizing records across Commonwealth + State/Territory jurisdictions.
3. Classifying operative status.
4. Recognizing and resolving legislation mentions.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Ingest up to 200 consolidated Acts for the Commonwealth
python -m src.pipeline.cli ingest --jurisdiction Cth --max-docs 200
```

### Notes on AustLII 403 responses

AustLII may intermittently return `403 Forbidden` for automated requests. The client now:

- sends browser-like headers and follows redirects,
- retries across common AustLII URL variants,
- records failed URLs to `data/state/failed_urls.jsonl`,
- and (by default) continues ingesting remaining URLs instead of crashing.

Use `--fail-fast` if you want the command to raise immediately.

### How ingestion works

`ingest` now has two stages:

1. discover legislation links from jurisdiction seed indexes, then
2. fetch each discovered legislation page (bounded by `--max-docs`).

CLI output includes discovered targets, successful ingests, and failures.


## Search ingested legislation

After ingesting, search local records from `data/processed/legislation.jsonl`:

Before filtering by `--status operative`, run classification to populate status values:

```bash
python -m src.pipeline.cli classify-operative --as-of 2026-04-27
```

```bash
python -m src.pipeline.cli search-legislation "privacy" --jurisdiction Cth --status operative --limit 10
```

Search results are de-duplicated by `source_id` so repeated ingests do not show the same Act multiple times.

For direct AustLII querying (no local cache), use live mode:

```bash
python -m src.pipeline.cli search-legislation "privacy" --live --jurisdiction Cth --status operative --max-docs 100 --limit 10
```

This mode is intended for Open-WebUI style online retrieval where fresh AustLII results are preferred over cached JSONL data.

## Layout

- `src/models/`: canonical schemas.
- `src/ingest/austlii/`: connectors and parsing.
- `src/classify/`: operative status logic.
- `src/nlp/`: mention extraction + resolver.
- `src/pipeline/`: workflow orchestration + CLI.
- `src/eval/`: evaluation utilities.
- `config/status_rules/`: jurisdiction-specific rules.
- `data/`: raw, processed, and stateful artifacts.
