"""Load an immutable catalog snapshot and reject inconsistent data before serving."""

import json
import re
from pathlib import Path

from pydantic import BaseModel, ValidationError

from roadmap_mcp.models import (
    CategoryFile,
    Industry,
    NamedEntity,
    Requirement,
    Role,
    Seniority,
    SeniorityFile,
    SkillFile,
    StoredSkill,
)


class CatalogError(ValueError):
    """Invalid catalog content; safe to display to a catalog editor."""


class LookupError(ValueError):
    """Unsupported user input; safe to display to an MCP client."""


def normalize(value: str) -> str:
    return re.sub(r"[\s_-]+", " ", value.strip().casefold())


def unique_index[N: NamedEntity](items: list[N], label: str) -> dict[str, N]:
    result: dict[str, N] = {}
    for item in items:
        if item.id in result:
            raise CatalogError(f"Duplicate {label} ID: {item.id}")
        result[item.id] = item
    if not result:
        raise CatalogError(f"No {label} entries found")
    return result


def alias_index[N: NamedEntity](items: dict[str, N], label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items.values():
        for alias in [item.id, item.name, *item.aliases]:
            key = normalize(alias)
            if key in result and result[key] != item.id:
                raise CatalogError(f"Ambiguous {label} alias: {alias}")
            result[key] = item.id
    return result


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


class Catalog:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.levels: dict[str, Seniority] = unique_index(
            self._read(self.directory / "seniority.json", SeniorityFile).levels, "seniority"
        )
        self.skills: dict[str, StoredSkill] = {}
        for file in self._files("skills"):
            for skill_id, skill in self._read(file, SkillFile).root.items():
                if skill_id in self.skills:
                    raise CatalogError(f"Duplicate skill ID: {skill_id}")
                self.skills[skill_id] = skill
        if not self.skills:
            raise CatalogError("No skill entries found")
        self.categories = self._read(self.directory / "categories.json", CategoryFile).root
        self.roles: dict[str, Role] = unique_index(
            [self._read(file, Role) for file in self._files("roles")], "role"
        )
        self.industries: dict[str, Industry] = unique_index(
            [self._read(file, Industry) for file in self._files("industries")], "industry"
        )
        self._aliases = {
            "role": alias_index(self.roles, "role"),
            "industry": alias_index(self.industries, "industry"),
            "seniority": alias_index(self.levels, "seniority"),
        }
        self._validate_references()

    def _files(self, folder: str) -> list[Path]:
        return sorted((self.directory / folder).glob("*.json"))

    def _read[T: BaseModel](self, file: Path, model: type[T]) -> T:
        try:
            raw = file.read_bytes()
            parsed = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
            result = model.model_validate(parsed)
        except (OSError, ValueError, ValidationError) as error:
            raise CatalogError(f"Invalid {file.relative_to(self.directory)}: {error}") from error
        return result

    def _validate_requirements(self, requirements: list[Requirement], origin: str) -> None:
        seen = set()
        for requirement in requirements:
            if requirement.skill_id not in self.skills:
                raise CatalogError(f"{origin}: unknown skill {requirement.skill_id}")
            if requirement.minimum_seniority not in self.levels:
                raise CatalogError(f"{origin}: unknown seniority {requirement.minimum_seniority}")
            if requirement.skill_id in seen:
                raise CatalogError(f"{origin}: duplicate requirement {requirement.skill_id}")
            seen.add(requirement.skill_id)

    def _validate_skill_metadata(self) -> None:
        names = {}
        for skill_id, skill in self.skills.items():
            name = normalize(skill.name)
            if name in names:
                raise CatalogError(
                    f"Duplicate skill name: {skill.name} ({names[name]} and {skill_id})"
                )
            names[name] = skill_id
            is_technology = skill.type not in {
                "implementation_capability",
                "professional_method",
                "soft_skill",
            }
            if is_technology and skill.technology_family is None:
                raise CatalogError(f"skill:{skill_id}: technology requires technology_family")
            if not is_technology and skill.technology_family is not None:
                raise CatalogError(f"skill:{skill_id}: technology_family requires a technology")
            if not is_technology and skill.selection_group is not None:
                raise CatalogError(f"skill:{skill_id}: selection_group requires a technology")
            if not is_technology and skill.technology_ecosystems:
                raise CatalogError(f"skill:{skill_id}: technology_ecosystems requires a technology")
            ecosystems = [normalize(name) for name in skill.technology_ecosystems]
            if len(set(ecosystems)) != len(ecosystems):
                raise CatalogError(f"skill:{skill_id}: duplicate technology ecosystem")
            seen = set()
            for capability_id in skill.related_capabilities:
                if capability_id in seen:
                    raise CatalogError(
                        f"skill:{skill_id}: duplicate related capability {capability_id}"
                    )
                if capability_id == skill_id:
                    raise CatalogError(f"skill:{skill_id}: self-related capability")
                capability = self.skills.get(capability_id)
                if capability is None:
                    raise CatalogError(
                        f"skill:{skill_id}: unknown related capability {capability_id}"
                    )
                if capability.type != "implementation_capability":
                    raise CatalogError(
                        f"skill:{skill_id}: related capability {capability_id} "
                        "must be an implementation_capability"
                    )
                seen.add(capability_id)

    def _validate_references(self) -> None:
        category_names = set()
        categorized = {}
        for category_id, category in self.categories.items():
            name = normalize(category.name)
            if name in category_names:
                raise CatalogError(f"Duplicate category name: {category.name}")
            category_names.add(name)
            for skill_id in category.skill_ids:
                if skill_id not in self.skills:
                    raise CatalogError(f"category:{category_id}: unknown skill {skill_id}")
                if skill_id in categorized:
                    raise CatalogError(
                        f"Skill {skill_id} must belong to exactly one category; "
                        f"listed in {categorized[skill_id]} and {category_id}"
                    )
                is_soft = self.skills[skill_id].type == "soft_skill"
                if is_soft != (category.type == "soft"):
                    raise CatalogError(
                        f"category:{category_id}: incompatible skill type {skill_id}"
                    )
                categorized[skill_id] = category_id
        missing = self.skills.keys() - categorized.keys()
        if missing:
            raise CatalogError(f"Skills without a category: {', '.join(sorted(missing))}")
        self.skill_categories = categorized
        self._validate_skill_metadata()
        if len({level.rank for level in self.levels.values()}) != len(self.levels):
            raise CatalogError("Seniority ranks must be unique")
        for role in self.roles.values():
            self._validate_requirements(role.requirements, f"role:{role.id}")
            requirements = {requirement.skill_id for requirement in role.requirements}
            seen = set()
            for option in role.skill_options:
                if option.skill_id not in requirements:
                    raise CatalogError(
                        f"role:{role.id}: skill option {option.skill_id} "
                        "must reference a role requirement"
                    )
                if option.skill_id in seen:
                    raise CatalogError(f"role:{role.id}: duplicate skill option {option.skill_id}")
                if self.skills[option.skill_id].type == "soft_skill":
                    raise CatalogError(f"role:{role.id}: soft skill option {option.skill_id}")
                seen.add(option.skill_id)
        for industry in self.industries.values():
            self._validate_requirements(industry.requirements, f"industry:{industry.id}")
            for role_id, requirements in industry.role_requirements.items():
                if role_id not in self.roles:
                    raise CatalogError(f"{industry.id}: unknown role {role_id}")
                self._validate_requirements(requirements, f"industry:{industry.id}/role:{role_id}")
        for role_id in self.roles:
            if not any(
                role_id in industry.role_requirements for industry in self.industries.values()
            ):
                raise CatalogError(f"Role {role_id} has no industry coverage")

    def resolve(self, dimension: str, value: str) -> str:
        resolved = self._aliases[dimension].get(normalize(value))
        if resolved is None:
            choices = ", ".join(sorted(set(self._aliases[dimension].values())))
            raise LookupError(
                f"Unknown {dimension}: {value!r}. Supported IDs: {choices}. "
                "Call list_catalog for names, aliases, and supported combinations."
            )
        return resolved
