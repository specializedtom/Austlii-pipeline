from __future__ import annotations

from datetime import date

import typer

from src.models.legislation import Jurisdiction
from src.pipeline import workflow

app = typer.Typer(help="AustLII legislation pipeline")


@app.command("ingest")
def ingest_cmd(jurisdiction: Jurisdiction = typer.Option(..., "--jurisdiction")) -> None:
    count = workflow.ingest(jurisdiction)
    typer.echo(f"Ingested {count} document(s) for {jurisdiction.value}")


@app.command("classify-operative")
def classify_cmd(as_of: str = typer.Option(date.today().isoformat(), "--as-of")) -> None:
    result = workflow.classify(date.fromisoformat(as_of))
    typer.echo(result)


@app.command("run-all")
def run_all_cmd(
    jurisdictions: list[Jurisdiction] = typer.Option([Jurisdiction.CTH], "--jurisdiction"),
    as_of: str = typer.Option(date.today().isoformat(), "--as-of"),
) -> None:
    for jurisdiction in jurisdictions:
        workflow.ingest(jurisdiction)
    workflow.classify(date.fromisoformat(as_of))
    typer.echo("Pipeline run complete")


if __name__ == "__main__":
    app()
