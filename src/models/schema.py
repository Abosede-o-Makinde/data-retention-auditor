"""Pydantic models for a data-schema retention inventory."""

from __future__ import annotations

from typing import Annotated, Iterator

from pydantic import BaseModel, Field, field_validator

SCHEMA_ID_PATTERN = r"^[A-Za-z0-9_-]{1,50}$"


class FieldRecord(BaseModel):
    """One column or property in a table, collection, or object type."""

    name: str = Field(min_length=1)
    personal_data: bool
    category: str = ""
    purpose: str = ""
    retention_period: str = ""
    trigger: str = ""
    disposal: str = ""
    deletion_job: bool | None = None
    erasure_supported: bool | None = None
    art89_exception: bool = False
    ropa_activity_id: str | None = None
    notes: str = ""


class Entity(BaseModel):
    """A table, collection, or object type that holds fields."""

    name: str = Field(min_length=1)
    description: str = ""
    fields: list[FieldRecord] = Field(min_length=1)


class SchemaInventory(BaseModel):
    """Declared data schema used to check retention metadata."""

    schema_id: Annotated[str, Field(pattern=SCHEMA_ID_PATTERN)]
    system: str = Field(min_length=1)
    organisation: str = ""
    schema_version: str = "1.0"
    notes: str = ""
    entities: list[Entity] = Field(min_length=1)

    @field_validator("schema_id")
    @classmethod
    def reject_path_traversal(cls, value: str) -> str:
        if ".." in value or "/" in value or "\\" in value:
            raise ValueError("schema_id must not contain path separators")
        return value

    def iter_personal_fields(self) -> Iterator[tuple[Entity, FieldRecord]]:
        for entity in self.entities:
            for field in entity.fields:
                if field.personal_data:
                    yield entity, field

    def personal_field_count(self) -> int:
        return sum(1 for _ in self.iter_personal_fields())
