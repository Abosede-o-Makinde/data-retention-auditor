"""Shared fixtures. Pytest loads this file automatically."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.auditor.parser import load_inventory
from src.models.schema import SchemaInventory

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def sample_data_dir() -> Path:
    return ROOT / "sample_data"


@pytest.fixture
def crm_path(sample_data_dir: Path) -> Path:
    return sample_data_dir / "crm_leads.json"


@pytest.fixture
def hr_path(sample_data_dir: Path) -> Path:
    return sample_data_dir / "hr_employees.json"


@pytest.fixture
def crm_inventory(crm_path: Path) -> SchemaInventory:
    return load_inventory(crm_path)


@pytest.fixture
def hr_inventory(hr_path: Path) -> SchemaInventory:
    return load_inventory(hr_path)
