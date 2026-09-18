"""Report writers for retention audits."""

from __future__ import annotations

import re
from pathlib import Path

DISCLAIMER = "Decision-support only. Not legal advice."
NO_GAPS = "No retention gaps on declared personal-data fields."


def safe_output_stem(schema_id: str) -> str:
    """Keep report filenames inside the output directory."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", schema_id.strip())
    return cleaned or "schema"


def prepare_output(path: Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target
