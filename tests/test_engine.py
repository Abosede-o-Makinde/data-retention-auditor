"""Tests for RET-01…08 and sample-inventory bands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.auditor.engine import DEFAULT_RULES_PATH, RetentionAuditor, RulesConfigError
from src.models.schema import Entity, FieldRecord, SchemaInventory


def _field(**overrides: object) -> FieldRecord:
    payload: dict = {
        "name": "email",
        "personal_data": True,
        "retention_period": "7 years after end of employment",
        "trigger": "end of employment",
        "disposal": "erase",
        "deletion_job": True,
        "erasure_supported": True,
        "art89_exception": False,
        "ropa_activity_id": "PA-001",
    }
    payload.update(overrides)
    return FieldRecord.model_validate(payload)


def _inventory(*fields: FieldRecord) -> SchemaInventory:
    return SchemaInventory(
        schema_id="T-1",
        system="Test",
        entities=[Entity(name="people", fields=list(fields))],
    )


@pytest.fixture
def auditor() -> RetentionAuditor:
    return RetentionAuditor()


def test_complete_field_has_no_findings(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field()))
    assert result.findings == []
    assert result.score == 100.0
    assert result.band == "PASS"


def test_ret01_empty_period(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field(retention_period="")))
    assert result.findings_for("RET-01")
    assert not result.findings_for("RET-02")
    assert not result.findings_for("RET-03")
    assert not result.findings_for("RET-04")
    assert result.band == "FAIL"


def test_ret02_vague_period(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field(retention_period="as per policy")))
    ids = [item.rule_id for item in result.findings]
    assert "RET-02" in ids
    assert "RET-01" not in ids
    assert result.band == "FAIL"


def test_ret03_missing_trigger(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field(trigger="")))
    assert result.findings_for("RET-03")
    assert result.band == "PARTIAL"


def test_ret04_deletion_job_not_true(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field(deletion_job=False)))
    assert result.findings_for("RET-04")
    assert result.band == "PARTIAL"


def test_ret05_missing_disposal(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field(disposal="")))
    assert result.findings_for("RET-05")
    assert result.band == "PARTIAL"


def test_ret06_erasure_not_supported(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field(erasure_supported=False)))
    assert result.findings_for("RET-06")
    assert result.band == "FAIL"


def test_ret07_indefinite_without_art89(auditor: RetentionAuditor) -> None:
    result = auditor.audit(
        _inventory(_field(retention_period="kept indefinitely", art89_exception=False))
    )
    assert result.findings_for("RET-07")
    assert result.band == "FAIL"


def test_ret07_indefinite_with_art89_skips_rule(auditor: RetentionAuditor) -> None:
    result = auditor.audit(
        _inventory(_field(retention_period="kept indefinitely", art89_exception=True))
    )
    assert not result.findings_for("RET-07")


def test_ret08_missing_ropa_link(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field(ropa_activity_id=None)))
    assert result.findings_for("RET-08")
    assert result.band == "PARTIAL"


def test_non_personal_fields_are_ignored(auditor: RetentionAuditor) -> None:
    result = auditor.audit(
        _inventory(
            _field(
                name="internal_id", personal_data=False, retention_period="", ropa_activity_id=None
            ),
            _field(),
        )
    )
    assert result.findings == []
    assert result.band == "PASS"


def test_no_personal_data_is_partial(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field(name="pk", personal_data=False, retention_period="")))
    assert result.score is None
    assert result.band == "PARTIAL"
    assert result.findings == []


def test_crm_sample_is_fail(auditor: RetentionAuditor, crm_inventory: SchemaInventory) -> None:
    result = auditor.audit(crm_inventory)
    assert result.band == "FAIL"
    locations = {item.location for item in result.findings_for("RET-01")}
    assert "leads.email" in locations
    vague = {item.location for item in result.findings_for("RET-02")}
    assert "leads.source_notes" in vague
    unenforced = {item.location for item in result.findings_for("RET-04")}
    assert "session_replays.blob" in unenforced
    assert not any(item.field == "lead_id" for item in result.findings)


def test_hr_sample_is_pass(auditor: RetentionAuditor, hr_inventory: SchemaInventory) -> None:
    result = auditor.audit(hr_inventory)
    assert result.findings == []
    assert result.score == 100.0
    assert result.band == "PASS"


def test_placeholder_trigger_is_ret03(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field(trigger="n/a")))
    assert result.findings_for("RET-03")


def test_placeholder_ropa_link_is_ret08(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field(ropa_activity_id="as per policy")))
    assert result.findings_for("RET-08")


def test_permanent_staff_is_not_indefinite(auditor: RetentionAuditor) -> None:
    result = auditor.audit(
        _inventory(_field(retention_period="7 years after end of employment for permanent staff"))
    )
    assert not result.findings_for("RET-07")
    assert result.band == "PASS"


def test_kept_permanently_is_indefinite(auditor: RetentionAuditor) -> None:
    result = auditor.audit(_inventory(_field(retention_period="kept permanently")))
    assert result.findings_for("RET-07")
    assert result.band == "FAIL"


def test_stacked_partial_findings_can_fail_on_score(auditor: RetentionAuditor) -> None:
    weak = dict(trigger="", deletion_job=False, disposal="", ropa_activity_id=None)
    result = auditor.audit(_inventory(_field(name="one", **weak), _field(name="two", **weak)))
    assert result.score is not None and result.score < 50
    assert all(item.severity == "PARTIAL" for item in result.findings)
    assert result.band == "FAIL"


def test_missing_rules_file_raises(tmp_path: Path) -> None:
    with pytest.raises(RulesConfigError, match="not found"):
        RetentionAuditor(config_path=tmp_path / "missing.json")


def test_invalid_rules_json_raises(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    path.write_text("{nope", encoding="utf-8")
    with pytest.raises(RulesConfigError, match="Invalid JSON"):
        RetentionAuditor(config_path=path)


def test_non_utf8_rules_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(RulesConfigError, match="UTF-8"):
        RetentionAuditor(config_path=path)


def test_rules_root_must_be_object(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(RulesConfigError, match="rules object"):
        RetentionAuditor(config_path=path)


def test_rules_payload_must_contain_rules(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({"schema_version": "1.0"}), encoding="utf-8")
    with pytest.raises(RulesConfigError, match="JSON array under 'rules'"):
        RetentionAuditor(config_path=path)


def test_rules_must_be_a_list(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({"rules": {"id": "RET-01"}}), encoding="utf-8")
    with pytest.raises(RulesConfigError, match="JSON array under 'rules'"):
        RetentionAuditor(config_path=path)


def test_phrase_lists_must_be_arrays(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))
    payload["vague_exact"] = "n/a"
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RulesConfigError, match="must be arrays"):
        RetentionAuditor(config_path=path)


def test_missing_rule_id_raises(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))
    payload["rules"] = [item for item in payload["rules"] if item["id"] != "RET-06"]
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RulesConfigError, match="missing rules"):
        RetentionAuditor(config_path=path)
