"""Stored editorial baselines and public bullet retrieval schemas."""

from typing import Annotated

from pydantic import Field

from roadmap_mcp.models import (
    CatalogEntry,
    Coverage,
    Identifier,
    Model,
    NamedEntity,
    Seniority,
    Text,
)

BulletCount = Annotated[int, Field(strict=True, ge=1, le=100)]


class BulletTaxonomy(Model):
    roles: list[NamedEntity] = Field(min_length=1)
    industries: list[NamedEntity] = Field(min_length=1)
    seniority_levels: list[Seniority] = Field(min_length=1)


class BulletManifest(Model):
    dataset: Text
    version: Text
    role_count: int = Field(ge=1)
    industry_count: int = Field(ge=1)
    seniority_levels: list[Identifier] = Field(min_length=1)
    bullet_count: int = Field(ge=1)


class BulletRecord(Model):
    id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]{0,79}$")]
    role_id: Identifier
    industry_id: Identifier
    seniority: Identifier
    focus: Text
    bullet: Text
    evidence_to_request: list[Text] = Field(min_length=1)


class BulletCatalogResult(Model):
    bullet_count: int
    roles: list[CatalogEntry]
    industries: list[CatalogEntry]
    seniority_levels: list[CatalogEntry]
    coverage: list[Coverage]


class BulletsResult(Model):
    role: CatalogEntry
    industry: CatalogEntry | None
    seniority_level: CatalogEntry
    requested_count: int
    returned_count: int
    available_count: int = Field(
        description="Unique bullets for this role at or above minimum seniority across industries."
    )
    bullets: list[BulletRecord]
