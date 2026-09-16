"""Tests for schema inventory JSON loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.auditor.parser import SchemaParseError, load_inventory
from src.models.schema import SchemaInventory


def test_load_crm_sample(crm_inventory: SchemaInventory) -> None:
    assert crm_inventory.schema_id == "CRM-001"
    assert crm_inventory.system == "Harbour Sales CRM"
    assert crm_inventory.personal_field_count() == 3
    emails = [
        field
        for entity, field in crm_inventory.iter_personal_fields()
        if entity.name == "leads" and field.name == "email"
    ]
    assert emails[0].retention_period == ""
    notes = [
        field
        for entity, field in crm_inventory.iter_personal_fields()
        if field.name == "source_notes"
    ]
    assert notes[0].retention_period == "as per policy"
    replay = [
        field
        for entity, field in crm_inventory.iter_personal_fields()
        if entity.name == "session_replays"
    ]
    assert replay[0].retention_period == "30 days"
    assert replay[0].deletion_job is False


def test_load_hr_sample(hr_inventory: SchemaInventory) -> None:
    assert hr_inventory.schema_id == "HR-001"
    assert hr_inventory.organisation == "Example Healthcare Trust"
    assert hr_inventory.personal_field_count() == 4
    names = {field.name for _, field in hr_inventory.iter_personal_fields()}
    assert names == {"full_name", "ni_number", "bank_details", "emergency_contact"}
    contact = next(
        field
        for _, field in hr_inventory.iter_personal_fields()
        if field.name == "emergency_contact"
    )
    assert contact.retention_period == "until employment ends"
    assert contact.trigger == "end of employment"
    assert contact.disposal == "erase"
    assert contact.deletion_job is True
    assert contact.erasure_supported is True
    assert contact.ropa_activity_id == "PA-001"


def test_non_personal_fields_are_not_counted(hr_inventory: SchemaInventory) -> None:
    employee_id = next(
        field
        for entity in hr_inventory.entities
        for field in entity.fields
        if field.name == "employee_id"
    )
    assert employee_id.personal_data is False


def test_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    with pytest.raises(SchemaParseError, match="not found"):
        load_inventory(missing)


def test_invalid_json_raises(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(SchemaParseError, match="Invalid JSON"):
        load_inventory(broken)


def test_json_array_raises(tmp_path: Path) -> None:
    path = tmp_path / "array.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(SchemaParseError, match="JSON object"):
        load_inventory(path)


def test_missing_required_fields_raises(tmp_path: Path) -> None:
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"schema_id": "X-1"}), encoding="utf-8")
    with pytest.raises(SchemaParseError, match="Invalid schema inventory"):
        load_inventory(path)


def test_empty_entities_raises(tmp_path: Path) -> None:
    path = tmp_path / "no_entities.json"
    path.write_text(
        json.dumps(
            {
                "schema_id": "X-1",
                "system": "Test",
                "entities": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(SchemaParseError, match="Invalid schema inventory"):
        load_inventory(path)


def test_schema_id_rejects_path_separators() -> None:
    with pytest.raises(ValidationError):
        SchemaInventory.model_validate(
            {
                "schema_id": "../escape",
                "system": "Test",
                "entities": [
                    {
                        "name": "t",
                        "fields": [{"name": "id", "personal_data": False}],
                    }
                ],
            }
        )
