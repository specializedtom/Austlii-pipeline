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

# Ingest starter run
python -m src.pipeline.cli ingest --jurisdiction Cth
```

### Notes on AustLII 403 responses

AustLII may intermittently return `403 Forbidden` for automated requests. The client now:

- sends browser-like headers and follows redirects,
- retries across common AustLII URL variants,
- records failed URLs to `data/state/failed_urls.jsonl`,
- and (by default) continues ingesting remaining URLs instead of crashing.

Use `--fail-fast` if you want the command to raise immediately.

## Layout

- `src/models/`: canonical schemas.
- `src/ingest/austlii/`: connectors and parsing.
- `src/classify/`: operative status logic.
- `src/nlp/`: mention extraction + resolver.
- `src/pipeline/`: workflow orchestration + CLI.
- `src/eval/`: evaluation utilities.
- `config/status_rules/`: jurisdiction-specific rules.
- `data/`: raw, processed, and stateful artifacts.
