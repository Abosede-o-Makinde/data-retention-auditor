"""Load a schema inventory from a local JSON file."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from src.models.schema import SchemaInventory


class SchemaParseError(ValueError):
    """Raised when a schema inventory file cannot be read or validated."""


def load_inventory(path: Path) -> SchemaInventory:
    """Parse `path` into a SchemaInventory.

    Rejects missing files, invalid JSON, non-objects, and payloads that do
    not match the inventory model.
    """
    if not path.is_file():
        raise SchemaParseError(f"Schema file not found: {path}")

    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SchemaParseError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise SchemaParseError(f"{path} must contain a JSON object")

    try:
        return SchemaInventory.model_validate(payload)
    except ValidationError as exc:
        raise SchemaParseError(f"Invalid schema inventory in {path}: {exc}") from exc
