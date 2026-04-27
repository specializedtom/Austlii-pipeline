from __future__ import annotations

from datetime import date

import typer

from src.models.legislation import Jurisdiction
from src.pipeline import workflow

app = typer.Typer(help="AustLII legislation pipeline")


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
