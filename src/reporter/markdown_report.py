"""Write audit findings as Markdown."""

from __future__ import annotations

from pathlib import Path

from src.auditor.engine import AuditResult, format_score
from src.reporter import DISCLAIMER, NO_GAPS, prepare_output


def _cell(value: str) -> str:
    return value.replace("|", "/")


def write_markdown(result: AuditResult, output_path: Path) -> Path:
    """Export findings, score, and band to a Markdown file."""
    target = prepare_output(output_path)
    inventory = result.inventory
    lines = [
        f"# Retention audit: {inventory.system}",
        "",
        f"- Schema ID: `{inventory.schema_id}`",
        f"- Organisation: {inventory.organisation or '—'}",
        f"- Personal-data fields: {inventory.personal_field_count()}",
        f"- Score: **{format_score(result.score)}**",
        f"- Band: **{result.band}**",
        f"- Findings: {len(result.findings)}",
        "",
    ]
    if inventory.notes:
        lines.extend([f"**Notes:** {inventory.notes}", ""])
    if not result.findings:
        lines.extend([NO_GAPS, ""])
    else:
        lines.extend(
            [
                "| Location | Rule | Severity | Articles | Issue |",
                "| -------- | ---- | -------- | -------- | ----- |",
            ]
        )
        for item in result.findings:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(item.location),
                        item.rule_id,
                        item.severity,
                        _cell(item.articles_label),
                        _cell(item.title),
                    ]
                )
                + " |"
            )
        lines.extend(["", "## Remediation", ""])
        for item in result.findings:
            lines.append(f"- **{item.location}** (`{item.rule_id}`): {item.remediation}")
        lines.append("")

    lines.extend(["---", DISCLAIMER, ""])
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
