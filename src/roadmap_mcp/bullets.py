"""Select deduplicated bullet baselines, prioritizing the requested industry."""

import json
from itertools import chain
from pathlib import Path

from pydantic import BaseModel, TypeAdapter

from roadmap_mcp.bullet_models import (
    BulletCatalogResult,
    BulletCount,
    BulletManifest,
    BulletRecord,
    BulletsResult,
    BulletTaxonomy,
)
from roadmap_mcp.catalog import (
    CatalogError,
    LookupError,
    alias_index,
    normalize,
    reject_duplicate_keys,
    unique_index,
)
from roadmap_mcp.models import Coverage
from roadmap_mcp.service import entry

COUNT_ADAPTER = TypeAdapter(BulletCount)


class BulletCatalog:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        taxonomy = self._read("catalog.json", BulletTaxonomy)
        self.roles = unique_index(taxonomy.roles, "bullet role")
        self.industries = unique_index(taxonomy.industries, "bullet industry")
        self.levels = unique_index(taxonomy.seniority_levels, "bullet seniority")
        self._aliases = {
            "role": alias_index(self.roles, "bullet role"),
            "industry": alias_index(self.industries, "bullet industry"),
            "seniority": alias_index(self.levels, "bullet seniority"),
        }
        if len({level.rank for level in self.levels.values()}) != len(self.levels):
            raise CatalogError("Bullet seniority ranks must be unique")
        self.manifest = self._read("manifest.json", BulletManifest)
        self.bullets = self._read_bullets()
        self.by_combination: dict[tuple[str, str, str], tuple[BulletRecord, ...]] = {}
        grouped: dict[tuple[str, str, str], list[BulletRecord]] = {}
        seen_ids: set[str] = set()
        for bullet in self.bullets:
            if bullet.id in seen_ids:
                raise CatalogError(f"Duplicate bullet ID: {bullet.id}")
            seen_ids.add(bullet.id)
            for label, identifier, entities in (
                ("role", bullet.role_id, self.roles),
                ("industry", bullet.industry_id, self.industries),
                ("seniority", bullet.seniority, self.levels),
            ):
                if identifier not in entities:
                    raise CatalogError(f"{bullet.id}: unknown {label} {identifier}")
            key = (bullet.role_id, bullet.industry_id, bullet.seniority)
            grouped.setdefault(key, []).append(bullet)
        self.by_combination = {key: tuple(rows) for key, rows in grouped.items()}
        self._validate_coverage()

    def _read[T: BaseModel](self, filename: str, model: type[T]) -> T:
        try:
            parsed = json.loads(
                (self.directory / filename).read_bytes(), object_pairs_hook=reject_duplicate_keys
            )
            return model.model_validate(parsed)
        except (OSError, ValueError) as error:
            raise CatalogError(f"Invalid bullets/{filename}: {error}") from error

    def _read_bullets(self) -> tuple[BulletRecord, ...]:
        _line_number = 0
        rows = []
        try:
            with (self.directory / "bullets.jsonl").open(encoding="utf-8") as stream:
                for _line_number, line in enumerate(stream, 1):
                    if line.strip():
                        parsed = json.loads(line, object_pairs_hook=reject_duplicate_keys)
                        rows.append(BulletRecord.model_validate(parsed))
        except (OSError, ValueError) as error:
            raise CatalogError(f"Invalid bullets/bullets.jsonl:{_line_number}: {error}") from error
        return tuple(rows)

    def _validate_coverage(self) -> None:
        manifest = self.manifest
        if (
            manifest.role_count != len(self.roles)
            or manifest.industry_count != len(self.industries)
            or manifest.bullet_count != len(self.bullets)
            or len(manifest.seniority_levels) != len(self.levels)
            or set(manifest.seniority_levels) != self.levels.keys()
        ):
            raise CatalogError("Bullet manifest counts or seniority levels disagree with data")
        for label, identifiers, used in (
            ("roles", self.roles, {row.role_id for row in self.bullets}),
            ("industries", self.industries, {row.industry_id for row in self.bullets}),
            ("seniority levels", self.levels, {row.seniority for row in self.bullets}),
        ):
            if identifiers.keys() != used:
                raise CatalogError(f"Bullet taxonomy contains {label} without bullets")

    def resolve(self, dimension: str, value: str) -> str:
        resolved = self._aliases[dimension].get(normalize(value))
        if resolved is None:
            choices = ", ".join(sorted(set(self._aliases[dimension].values())))
            raise LookupError(
                f"Unknown bullet {dimension}: {value!r}. Supported IDs: {choices}. "
                "Call list_bullet_catalog for names, aliases, and supported combinations."
            )
        return resolved


class BulletService:
    def __init__(self, catalog: BulletCatalog):
        self.catalog = catalog

    def list_bullet_catalog(self) -> BulletCatalogResult:
        catalog = self.catalog
        pairs = {(role, industry) for role, industry, _ in catalog.by_combination}
        return BulletCatalogResult(
            bullet_count=len(catalog.bullets),
            roles=[entry(role) for role in catalog.roles.values()],
            industries=[entry(industry) for industry in catalog.industries.values()],
            seniority_levels=[
                entry(level)
                for level in sorted(catalog.levels.values(), key=lambda level: level.rank)
            ],
            coverage=[
                Coverage(
                    role_id=role_id,
                    industry_ids=[
                        industry_id
                        for industry_id in catalog.industries
                        if (role_id, industry_id) in pairs
                    ],
                )
                for role_id in catalog.roles
            ],
        )

    def get_bullets(
        self,
        role_name: str,
        industry: str | None = None,
        seniority_level: str | None = "junior",
        count: int = 5,
    ) -> BulletsResult:
        count = COUNT_ADAPTER.validate_python(count)
        catalog = self.catalog
        role = catalog.roles[catalog.resolve("role", role_name)]
        sector = (
            catalog.industries[catalog.resolve("industry", industry)]
            if industry is not None
            else None
        )
        level = catalog.levels[
            catalog.resolve(
                "seniority", seniority_level if seniority_level is not None else "junior"
            )
        ]
        eligible = [
            bullet
            for bullet in catalog.bullets
            if bullet.role_id == role.id and catalog.levels[bullet.seniority].rank >= level.rank
        ]
        candidates = (
            chain(
                (bullet for bullet in eligible if bullet.industry_id == sector.id),
                (bullet for bullet in eligible if bullet.industry_id != sector.id),
            )
            if sector is not None
            else eligible
        )
        unique = []
        seen = set()
        for bullet in candidates:
            text = " ".join(bullet.bullet.split()).casefold()
            if text not in seen:
                unique.append(bullet)
                seen.add(text)
        bullets = unique[:count]
        return BulletsResult(
            role=entry(role),
            industry=entry(sector) if sector is not None else None,
            seniority_level=entry(level),
            requested_count=count,
            returned_count=len(bullets),
            available_count=len(unique),
            bullets=bullets,
        )
