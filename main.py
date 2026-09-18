"""data-retention-auditor CLI entry point."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src import __version__
from src.auditor.engine import AuditResult, RetentionAuditor, RulesConfigError, format_score
from src.auditor.parser import SchemaParseError, load_inventory
from src.reporter import NO_GAPS, safe_output_stem
from src.reporter.json_report import write_json
from src.reporter.markdown_report import write_markdown
from src.reporter.pdf_report import RetentionPdfReport

console = Console()
DEFAULT_OUTPUT_DIR = Path("outputs")


def _style_for(label: str) -> str:
    if label == "FAIL":
        return "red"
    if label == "PARTIAL":
        return "yellow"
    return "green"


def _audit(input_path: Path) -> AuditResult:
    return RetentionAuditor().audit(load_inventory(input_path))


def _print_summary(result: AuditResult) -> None:
    inventory = result.inventory
    colour = _style_for(result.band)
    lines = []
    if inventory.organisation:
        lines.append(f"Organisation: {inventory.organisation}")
    lines.extend(
        [
            f"System: [bold]{inventory.system}[/bold]",
            f"Schema ID: {inventory.schema_id}",
            f"Personal-data fields: {inventory.personal_field_count()}",
            f"Score: [bold]{format_score(result.score)}[/bold]",
            f"Band: [bold {colour}]{result.band}[/bold {colour}]",
            f"Findings: {len(result.findings)}",
        ]
    )
    console.print(Panel("\n".join(lines), title="Retention audit"))


def _print_findings(result: AuditResult) -> None:
    if not result.findings:
        console.print(f"[green]{NO_GAPS}[/green]")
        return
    table = Table(title="Findings")
    table.add_column("Location")
    table.add_column("Rule")
    table.add_column("Severity")
    table.add_column("Articles")
    table.add_column("Issue")
    for item in result.findings:
        colour = _style_for(item.severity)
        table.add_row(
            item.location,
            item.rule_id,
            f"[{colour}]{item.severity}[/{colour}]",
            item.articles_label,
            item.title,
        )
    console.print(table)


def _write_reports(result: AuditResult, output_dir: Path) -> None:
    stem = safe_output_stem(result.inventory.schema_id)
    markdown_path = write_markdown(result, output_dir / f"{stem}_findings.md")
    json_path = write_json(result, output_dir / f"{stem}_findings.json")
    pdf_path = RetentionPdfReport().generate(result, output_dir / f"{stem}_report.pdf")
    console.print(
        Panel(
            f"Markdown: {markdown_path}\nJSON: {json_path}\nPDF: {pdf_path}",
            title="Report export",
        )
    )


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["scan", "score", "report"]),
    default="scan",
    show_default=True,
    help="Workflow mode to run.",
)
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(path_type=Path),
    help="JSON schema inventory.",
)
@click.option(
    "--output",
    "output_dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    show_default=True,
    help="Directory for Markdown, JSON, and PDF outputs.",
)
@click.version_option(version=__version__, prog_name="data-retention-auditor")
def cli(mode: str, input_path: Path, output_dir: Path) -> None:
    """Scan data schemas for missing retention periods (UK GDPR Art. 5(1)(e))."""
    try:
        result = _audit(input_path)
        _print_summary(result)
        if mode in {"scan", "report"}:
            _print_findings(result)
        if mode == "report":
            _write_reports(result, output_dir)
    except (SchemaParseError, RulesConfigError, OSError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    cli()
