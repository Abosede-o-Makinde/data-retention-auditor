"""Retention audit PDF via fpdf2."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fpdf import FPDF

from src import __version__
from src.auditor.engine import AuditResult, format_score
from src.reporter import DISCLAIMER, NO_GAPS, prepare_output

_BAND_FILL = {
    "PASS": (0, 128, 0),
    "PARTIAL": (200, 120, 0),
    "FAIL": (160, 0, 0),
}


class RetentionPdfReport:
    """Writes a short A4 PDF from an audit result."""

    MARGIN = 20
    DARK_BLUE = (31, 56, 100)
    WHITE = (255, 255, 255)
    LIGHT_GREY = (245, 245, 245)
    TEXT_DARK = (30, 30, 30)

    def generate(self, result: AuditResult, output_path: Path) -> Path:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=self.MARGIN)
        pdf.set_margins(self.MARGIN, self.MARGIN, self.MARGIN)
        self._add_cover(pdf, result)
        self._add_findings(pdf, result)
        target = prepare_output(output_path)
        pdf.output(str(target.resolve()))
        return target

    def _add_cover(self, pdf: FPDF, result: AuditResult) -> None:
        inventory = result.inventory
        pdf.add_page()
        pdf.set_fill_color(*self.DARK_BLUE)
        pdf.rect(0, 0, 210, 45, style="F")
        pdf.set_text_color(*self.WHITE)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_y(12)
        pdf.cell(0, 10, "data-retention-auditor", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        pdf.cell(
            0,
            8,
            f"UK GDPR Art. 5(1)(e) scan v{__version__}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_text_color(*self.TEXT_DARK)
        pdf.ln(18)
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 10, "Retention audit", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        self._row(pdf, "System", inventory.system)
        self._row(pdf, "Schema ID", inventory.schema_id)
        if inventory.organisation:
            self._row(pdf, "Organisation", inventory.organisation)
        self._row(pdf, "Personal-data fields", str(inventory.personal_field_count()))
        self._row(pdf, "Score", format_score(result.score))
        self._row(pdf, "Findings", str(len(result.findings)))
        self._row(pdf, "Generated (UTC)", datetime.now(UTC).strftime("%Y-%m-%d %H:%M"))

        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(35, 8, "Overall band:")
        pdf.set_fill_color(*_BAND_FILL[result.band])
        pdf.set_text_color(*self.WHITE)
        pdf.cell(40, 8, result.band, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*self.TEXT_DARK)
        pdf.ln(8)
        pdf.set_font("Helvetica", "I", 9)
        self._para(pdf, DISCLAIMER)

    def _add_findings(self, pdf: FPDF, result: AuditResult) -> None:
        pdf.add_page()
        self._header(pdf, "Findings")
        if not result.findings:
            self._para(pdf, NO_GAPS)
            return
        for item in result.findings:
            pdf.set_font("Helvetica", "B", 10)
            self._para(
                pdf,
                f"{item.location}  {item.rule_id}  {item.severity}  {item.articles_label}",
            )
            pdf.set_font("Helvetica", size=9)
            self._para(pdf, item.title)
            self._para(pdf, item.remediation)
            pdf.ln(2)

    def _header(self, pdf: FPDF, title: str) -> None:
        pdf.set_fill_color(*self.LIGHT_GREY)
        pdf.set_text_color(*self.DARK_BLUE)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, self._safe(title), fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_text_color(*self.TEXT_DARK)

    def _row(self, pdf: FPDF, key: str, value: str) -> None:
        pdf.set_x(self.MARGIN)
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(0, 6, self._safe(f"{key}: {value}"), new_x="LMARGIN", new_y="NEXT")

    def _para(self, pdf: FPDF, text: str) -> None:
        pdf.set_x(self.MARGIN)
        pdf.multi_cell(0, 5, self._safe(text), new_x="LMARGIN", new_y="NEXT")

    @staticmethod
    def _safe(text: str) -> str:
        cleaned = (
            text.replace("\u2014", "-")
            .replace("\u2013", "-")
            .replace("\u2022", "-")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
        )
        return cleaned.encode("latin-1", errors="replace").decode("latin-1")
