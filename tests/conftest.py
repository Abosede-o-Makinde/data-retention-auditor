"""Shared fixtures. Pytest loads this file automatically."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.auditor.parser import load_inventory
from src.models.schema import SchemaInventory

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def crm_inventory() -> SchemaInventory:
    return load_inventory(ROOT / "sample_data" / "crm_leads.json")


@pytest.fixture
def hr_inventory() -> SchemaInventory:
    return load_inventory(ROOT / "sample_data" / "hr_employees.json")
