"""CLI interface for CSGR-Lab using Typer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from csgr_lab import __version__
from csgr_lab.config.settings import Settings
from csgr_lab.contracts.schema import ContractSpec
from csgr_lab.evidence.logger import EvidenceLogger
from csgr_lab.scoring.engine import ScoringEngine

app = typer.Typer(
    name="csgr",
    help="CSGR-Lab: Contracted Stability & Drift Measurement for LLMs.",
    no_args_is_help=True,
)


@app.command()
def score(
    contract_path: Path = typer.Argument(..., help="Path to contract JSON file"),
    measurements_path: Path = typer.Argument(..., help="Path to measurements JSON file"),
    evidence_dir: Path = typer.Option(None, help="Override evidence output directory"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Score a contract against measurements."""
    settings = Settings()
    if evidence_dir:
        settings = Settings(evidence_dir=evidence_dir)

    contract_data = json.loads(contract_path.read_text())
    contract = ContractSpec(**contract_data)

    measurements = json.loads(measurements_path.read_text())

    engine = ScoringEngine()
    run = engine.score(contract, measurements)

    logger = EvidenceLogger(settings.evidence_path)
    logger.log(run.to_dict())

    if json_output:
        typer.echo(json.dumps(run.to_dict(), indent=2))
    else:
        status = run.result.status.value.upper()
        typer.echo(f"Contract: {contract.name}")
        typer.echo(f"Status:   {status}")
        typer.echo(f"Pass: {run.result.pass_count} | "
                   f"Fail: {run.result.fail_count} | "
                   f"Warn: {run.result.warn_count}")
        typer.echo(f"Run ID:   {run.run_id}")
        typer.echo(f"Hash:     {run.input_hash[:16]}...")

    if run.result.status.value == "fail":
        raise typer.Exit(code=1)


@app.command()
def verify(
    evidence_dir: Path = typer.Option(None, help="Override evidence directory"),
) -> None:
    """Verify the integrity of the evidence chain."""
    settings = Settings()
    if evidence_dir:
        settings = Settings(evidence_dir=evidence_dir)

    logger = EvidenceLogger(settings.evidence_path)
    is_valid, count, detail = logger.verify_chain()

    if is_valid:
        typer.echo(f"VALID: {detail}")
    else:
        typer.echo(f"INVALID: {detail}", err=True)
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Show CSGR-Lab version."""
    typer.echo(f"csgr-lab {__version__}")


if __name__ == "__main__":
    app()
