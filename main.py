"""data-retention-auditor CLI entry point (scaffold)."""

from __future__ import annotations

import click

from src import __version__


@click.group()
@click.version_option(version=__version__, prog_name="data-retention-auditor")
def cli() -> None:
    """Scan data schemas for missing retention periods (UK GDPR Art. 5(1)(e))."""


@cli.command()
def scan() -> None:
    """Scan a schema for missing retention periods."""
    click.echo("scan is not implemented yet — repository scaffold only.")


if __name__ == "__main__":
    cli()
