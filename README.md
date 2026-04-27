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

- sends browser-like headers (including the AustLII search Referer) and follows redirects,
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

`search-legislation` now defaults to direct AustLII live access (no local cache):

```bash
python -m src.pipeline.cli search-legislation "privacy" --jurisdiction Cth --status operative --max-docs 100 --limit 10
```

Use `--no-live` to force local cached JSONL search.

This default is intended for Open-WebUI style online retrieval where fresh AustLII results are preferred over cached data.

You can also search within body text (e.g., Division/Section/Clause references):

```bash
python -m src.pipeline.cli search-legislation "section 5" --jurisdiction Cth --status operative --limit 5
```

The CLI prints matching text snippets under each result.

## Verify citations in free text

You can verify extracted legislation citations against AustLII title search:

```bash
python -m src.pipeline.cli verify-text "Under the Privacy Act 1988 and Evidence Act 1995..." --jurisdiction Cth --limit 5
```

This is adapted from verifier-style workflows: it extracts citation candidates, queries AustLII, and reports verified vs unverified citations.

If AustLII title search is blocked (e.g., HTTP 403), verifier mode falls back to live legislation-page lookup within the selected jurisdiction.

## Layout

- `src/models/`: canonical schemas.
- `src/ingest/austlii/`: connectors and parsing.
- `src/classify/`: operative status logic.
- `src/nlp/`: mention extraction + resolver.
- `src/pipeline/`: workflow orchestration + CLI.
- `src/eval/`: evaluation utilities.
- `config/status_rules/`: jurisdiction-specific rules.
- `data/`: raw, processed, and stateful artifacts.
