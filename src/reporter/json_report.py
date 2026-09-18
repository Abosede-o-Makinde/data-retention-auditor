"""Write audit findings as JSON."""

from __future__ import annotations

import json
from pathlib import Path

from src.auditor.engine import AuditResult
from src.reporter import DISCLAIMER, prepare_output


def write_json(result: AuditResult, output_path: Path) -> Path:
    """Export a machine-readable audit result."""
    target = prepare_output(output_path)
    inventory = result.inventory
    payload = {
        "schema_id": inventory.schema_id,
        "system": inventory.system,
        "organisation": inventory.organisation,
        "score": result.score,
        "band": result.band,
        "personal_fields": inventory.personal_field_count(),
        "finding_count": len(result.findings),
        "findings": [item.to_dict() for item in result.findings],
        "disclaimer": DISCLAIMER,
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target
