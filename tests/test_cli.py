"""CLI smoke tests for scan, score, and report modes."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from main import cli

ROOT = Path(__file__).resolve().parents[1]
CRM = ROOT / "sample_data" / "crm_leads.json"
HR = ROOT / "sample_data" / "hr_employees.json"


def test_scan_crm_is_fail() -> None:
    result = CliRunner().invoke(cli, ["--mode", "scan", "--input", str(CRM)])
    assert result.exit_code == 0, result.output
    assert "FAIL" in result.output
    assert "leads.email" in result.output
    assert "RET-01" in result.output


def test_score_hr_is_pass() -> None:
    result = CliRunner().invoke(cli, ["--mode", "score", "--input", str(HR)])
    assert result.exit_code == 0, result.output
    assert "PASS" in result.output
    assert "100" in result.output
    assert "leads.email" not in result.output


def test_report_writes_markdown_json_and_pdf(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = Path("out")
    result = CliRunner().invoke(
        cli,
        ["--mode", "report", "--input", str(HR), "--output", str(out)],
    )
    assert result.exit_code == 0, result.output
    markdown = out / "HR-001_findings.md"
    assert markdown.is_file()
    assert (out / "HR-001_findings.json").is_file()
    pdf = out / "HR-001_report.pdf"
    assert pdf.is_file()
    assert pdf.stat().st_size > 500
    text = markdown.read_text(encoding="utf-8")
    assert "PASS" in text
    assert "Decision-support only" in text


def test_report_crm_includes_findings(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        cli,
        ["--mode", "report", "--input", str(CRM), "--output", "out"],
    )
    assert result.exit_code == 0, result.output
    text = Path("out/CRM-001_findings.md").read_text(encoding="utf-8")
    assert "FAIL" in text
    assert "leads.email" in text
    assert "RET-01" in text


def test_missing_input_fails(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["--mode", "scan", "--input", "missing.json"])
    assert result.exit_code == 1
    assert "Error" in result.output
