"""Retention rules engine and scoring (UK GDPR Arts. 5(1)(e), 17, 30)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.models.schema import Entity, FieldRecord, SchemaInventory

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[2] / "config" / "retention_rules.json"
REQUIRED_RULE_IDS = tuple(f"RET-{index:02d}" for index in range(1, 9))


class RulesConfigError(ValueError):
    """Raised when retention_rules.json cannot be loaded."""


@dataclass(frozen=True)
class RuleSpec:
    id: str
    severity: str
    weight: int
    articles: tuple[str, ...]
    title: str
    remediation: str


@dataclass
class Finding:
    rule_id: str
    entity: str
    field: str
    severity: str
    title: str
    articles: tuple[str, ...]
    weight: int
    remediation: str

    @property
    def location(self) -> str:
        return f"{self.entity}.{self.field}"

    @property
    def articles_label(self) -> str:
        return ", ".join(f"Art. {a}" for a in self.articles)

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "location": self.location,
            "severity": self.severity,
            "title": self.title,
            "articles": list(self.articles),
            "weight": self.weight,
            "remediation": self.remediation,
        }


@dataclass
class AuditResult:
    inventory: SchemaInventory
    findings: list[Finding]
    score: float | None
    band: str

    def findings_for(self, rule_id: str) -> list[Finding]:
        return [item for item in self.findings if item.rule_id == rule_id]


def band_for(score: float | None, findings: list[Finding]) -> str:
    """FAIL if any FAIL finding or the score drops below 50; else PARTIAL or PASS."""
    if score is None:
        return "PARTIAL"
    if any(item.severity == "FAIL" for item in findings) or score < 50:
        return "FAIL"
    if findings:
        return "PARTIAL"
    return "PASS"


def format_score(score: float | None) -> str:
    return "n/a" if score is None else f"{score}/100"


def _normalise(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def _contains_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    """Match whole phrases. 'permanent staff' must not trip 'semi-permanent'."""
    for phrase in phrases:
        pattern = r"(?<![a-z0-9-])" + re.escape(phrase) + r"(?![a-z0-9-])"
        if re.search(pattern, text):
            return True
    return False


class RetentionAuditor:
    """Score personal-data fields in a schema inventory against RET-01…08."""

    def __init__(self, config_path: Path | None = None) -> None:
        payload = _load_rules_payload(config_path or DEFAULT_RULES_PATH)
        self.vague_exact = payload["vague_exact"]
        self.vague_phrases = payload["vague_phrases"]
        self.indefinite_phrases = payload["indefinite_phrases"]
        self.rules = {spec.id: spec for spec in payload["parsed_rules"]}

    def audit(self, inventory: SchemaInventory) -> AuditResult:
        personal_fields = list(inventory.iter_personal_fields())
        if not personal_fields:
            return AuditResult(
                inventory=inventory, findings=[], score=None, band=band_for(None, [])
            )

        findings: list[Finding] = []
        for entity, field in personal_fields:
            findings.extend(self._evaluate_field(entity, field))
        score = round(max(0.0, 100.0 - sum(item.weight for item in findings)), 1)
        return AuditResult(
            inventory=inventory,
            findings=findings,
            score=score,
            band=band_for(score, findings),
        )

    def _evaluate_field(self, entity: Entity, field: FieldRecord) -> list[Finding]:
        period = _normalise(field.retention_period)
        empty = period == ""
        vague = (not empty) and self._is_placeholder(period)
        usable_period = (not empty) and (not vague)

        findings: list[Finding] = []
        if empty:
            findings.append(self._finding("RET-01", entity, field))
        elif vague:
            findings.append(self._finding("RET-02", entity, field))
        elif self._is_indefinite(period) and not field.art89_exception:
            findings.append(self._finding("RET-07", entity, field))

        if usable_period and self._is_placeholder(field.trigger):
            findings.append(self._finding("RET-03", entity, field))
        if usable_period and field.deletion_job is not True:
            findings.append(self._finding("RET-04", entity, field))
        if self._is_placeholder(field.disposal):
            findings.append(self._finding("RET-05", entity, field))
        if field.erasure_supported is not True:
            findings.append(self._finding("RET-06", entity, field))
        if self._is_placeholder(field.ropa_activity_id):
            findings.append(self._finding("RET-08", entity, field))
        return findings

    def _is_placeholder(self, value: str | None) -> bool:
        text = _normalise(value)
        if text == "" or text in self.vague_exact:
            return True
        return _contains_phrase(text, self.vague_phrases)

    def _is_indefinite(self, period: str) -> bool:
        return _contains_phrase(period, self.indefinite_phrases)

    def _finding(self, rule_id: str, entity: Entity, field: FieldRecord) -> Finding:
        spec = self.rules[rule_id]
        return Finding(
            rule_id=spec.id,
            entity=entity.name,
            field=field.name,
            severity=spec.severity,
            title=spec.title,
            articles=spec.articles,
            weight=spec.weight,
            remediation=spec.remediation,
        )


def _load_rules_payload(path: Path) -> dict:
    if not path.is_file():
        raise RulesConfigError(f"Rules file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise RulesConfigError(f"Could not decode {path} as UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RulesConfigError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RulesConfigError(f"{path} must contain a rules object")

    rules_raw = payload.get("rules")
    if not isinstance(rules_raw, list):
        raise RulesConfigError(f"{path} must contain a JSON array under 'rules'")

    try:
        vague_exact = payload["vague_exact"]
        vague_phrases = payload["vague_phrases"]
        indefinite_phrases = payload["indefinite_phrases"]
        if not all(
            isinstance(value, list) for value in (vague_exact, vague_phrases, indefinite_phrases)
        ):
            raise TypeError("vague_exact, vague_phrases, and indefinite_phrases must be arrays")
        rules = [_rule_spec(item) for item in rules_raw]
        parsed = {
            "vague_exact": {item.lower() for item in vague_exact},
            "vague_phrases": tuple(item.lower() for item in vague_phrases),
            "indefinite_phrases": tuple(item.lower() for item in indefinite_phrases),
            "parsed_rules": rules,
        }
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise RulesConfigError(f"Invalid rules config in {path}: {exc}") from exc

    found = {spec.id for spec in rules}
    missing = [rule_id for rule_id in REQUIRED_RULE_IDS if rule_id not in found]
    if missing:
        raise RulesConfigError(f"{path} is missing rules: {', '.join(missing)}")
    return parsed


def _rule_spec(item: dict) -> RuleSpec:
    return RuleSpec(
        id=item["id"],
        severity=item["severity"],
        weight=int(item["weight"]),
        articles=tuple(item["articles"]),
        title=item["title"],
        remediation=item["remediation"],
    )
