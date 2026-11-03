"""Select relevant skills from role, industry, and seniority rules."""

from roadmap_mcp.catalog import Catalog, LookupError
from roadmap_mcp.models import (
    CatalogEntry,
    CatalogResult,
    Coverage,
    NamedEntity,
    Roadmap,
    SkillCategory,
    SkillNameOnly,
)


def entry(entity: NamedEntity) -> CatalogEntry:
    return CatalogEntry(id=entity.id, name=entity.name, aliases=entity.aliases)


class RoadmapService:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def list_catalog(self) -> CatalogResult:
        catalog = self.catalog
        return CatalogResult(
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
                        i.id for i in catalog.industries.values() if role_id in i.role_requirements
                    ],
                )
                for role_id in catalog.roles
            ],
        )

    def get_roadmap(
        self,
        role_name: str,
        industry: str,
        seniority_level: str,
        include_descriptions: bool = True,
    ) -> Roadmap:
        catalog = self.catalog
        role = catalog.roles[catalog.resolve("role", role_name)]
        sector = catalog.industries[catalog.resolve("industry", industry)]
        level = catalog.levels[catalog.resolve("seniority", seniority_level)]
        if role.id not in sector.role_requirements:
            raise LookupError(
                f"No roadmap for {role.name} in {sector.name}. "
                "Call list_catalog for supported combinations."
            )

        selected = {}
        for requirements in (
            role.requirements,
            sector.requirements,
            sector.role_requirements[role.id],
        ):
            for requirement in requirements:
                if catalog.levels[requirement.minimum_seniority].rank <= level.rank:
                    selected[requirement.skill_id] = catalog.skills[requirement.skill_id]

        grouped = {}
        for skill_id, skill in selected.items():
            category_id = catalog.skill_categories[skill_id]
            grouped.setdefault(category_id, []).append(
                skill if include_descriptions else SkillNameOnly(name=skill.name)
            )

        by_type = {"hard": [], "soft": []}
        for category_id, category in catalog.categories.items():
            if category_id in grouped:
                by_type[category.type].append(
                    SkillCategory(name=category.name, skills=grouped[category_id])
                )

        return Roadmap(hard_skills=by_type["hard"], soft_skills=by_type["soft"])
