from __future__ import annotations

from datetime import date

import typer

from src.models.legislation import Jurisdiction
from src.pipeline import workflow
from src.pipeline.search import load_records, search_records
from src.pipeline.verifier import verify_text_citations

app = typer.Typer(help="AustLII legislation pipeline")


def _parse_jurisdiction(value: str) -> Jurisdiction:
    normalized = value.strip()
    for candidate in Jurisdiction:
        if candidate.value.lower() == normalized.lower() or candidate.name.lower() == normalized.lower():
            return candidate
    raise typer.BadParameter(f"Unknown jurisdiction: {value}")


@app.command("ingest")
def ingest_cmd(
    jurisdiction: Jurisdiction = typer.Option(..., "--jurisdiction"),
    fail_fast: bool = typer.Option(False, "--fail-fast", help="Raise immediately on first fetch failure."),
    max_docs: int = typer.Option(100, "--max-docs", min=1, help="Maximum number of legislation pages to ingest."),
) -> None:
    result = workflow.ingest(jurisdiction, fail_fast=fail_fast, max_docs=max_docs)
    typer.echo(
        f"Ingest completed for {result['jurisdiction']}: "
        f"targets={result['targets_discovered']}, "
        f"ingested={result['records_ingested']}, failed={result['records_failed']}"
    )


@app.command("classify-operative")
def classify_cmd(as_of: str = typer.Option(date.today().isoformat(), "--as-of")) -> None:
    result = workflow.classify(date.fromisoformat(as_of))
    typer.echo(result)


@app.command("search-legislation")
def search_legislation_cmd(
    query: str = typer.Argument(..., help="Search text for legislation title/citation/source id."),
    jurisdiction: str | None = typer.Option(None, "--jurisdiction", help="Optional jurisdiction filter, e.g. Cth."),
    status: str | None = typer.Option(None, "--status", help="Optional status filter, e.g. operative."),
    limit: int = typer.Option(20, "--limit", min=1, help="Max number of results."),
    live: bool = typer.Option(False, "--live", help="Query AustLII directly without local cache."),
    max_docs: int = typer.Option(100, "--max-docs", min=1, help="When --live is set, max docs to scan."),
    as_of: str = typer.Option(date.today().isoformat(), "--as-of", help="Classification date for --live mode."),
) -> None:
    if live:
        if not jurisdiction:
            raise typer.BadParameter("--jurisdiction is required with --live")
        live_matches = workflow.query_live(
            query=query,
            jurisdiction=_parse_jurisdiction(jurisdiction),
            status=status,
            max_docs=max_docs,
            as_of=date.fromisoformat(as_of),
        )
        matches = live_matches[:limit]
    else:
        records = load_records()
        matches = search_records(query, records, jurisdiction=jurisdiction, status=status, limit=limit)
        if not matches:
            typer.echo("No matches found.")
            if status and records:
                typer.echo("Tip: run `classify-operative` first, then retry status-filtered search.")
            return

    if not matches:
        typer.echo("No matches found.")
        return

    typer.echo(f"Found {len(matches)} result(s):")
    for item in matches:
        typer.echo(
            " - {title} [{jur}] status={status} source_id={source}".format(
                title=item.get("short_title", item.get("title", "<untitled>")),
                jur=item.get("jurisdiction", "<unknown>"),
                status=item.get("status", "unknown"),
                source=item.get("source_id", "<none>"),
            )
        )
        for snippet in item.get("snippets", [])[:3]:
            typer.echo(f"    > {snippet}")


@app.command("verify-text")
def verify_text_cmd(
    text: str = typer.Argument(..., help="Free text containing possible legislation citations."),
    limit: int = typer.Option(5, "--limit", min=1, help="Maximum citations to verify."),
) -> None:
    result = verify_text_citations(text, limit=limit)
    typer.echo(f"Citations found: {result['citations_found']}")

    if result["verified"]:
        typer.echo("Verified:")
        for item in result["verified"]:
            r = item["result"]
            typer.echo(f" - {item['citation']} -> {r.get('title')} ({r.get('url')})")

    if result["unverified"]:
        typer.echo("Unverified:")
        for item in result["unverified"]:
            r = item["result"]
            typer.echo(f" - {item['citation']} ({r.get('error', 'not found')})")


@app.command("run-all")
def run_all_cmd(
    jurisdictions: list[Jurisdiction] = typer.Option([Jurisdiction.CTH], "--jurisdiction"),
    as_of: str = typer.Option(date.today().isoformat(), "--as-of"),
    fail_fast: bool = typer.Option(False, "--fail-fast"),
    max_docs: int = typer.Option(100, "--max-docs", min=1),
) -> None:
    for jurisdiction in jurisdictions:
        workflow.ingest(jurisdiction, fail_fast=fail_fast, max_docs=max_docs)
    workflow.classify(date.fromisoformat(as_of))
    typer.echo("Pipeline run complete")


if __name__ == "__main__":
    app()
