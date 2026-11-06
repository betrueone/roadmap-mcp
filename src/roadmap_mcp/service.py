"""Select relevant skills from role, industry, and seniority rules."""

from roadmap_mcp.catalog import Catalog, LookupError
from roadmap_mcp.models import (
    CatalogEntry,
    CatalogResult,
    Coverage,
    DescribedRankedSkill,
    NamedEntity,
    RankedSkill,
    Requirement,
    Roadmap,
    Skill,
    SkillCategory,
    SkillLimit,
    SkillNameOnly,
    SkillsResult,
)
from roadmap_mcp.skill_categories import response_category


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
                Skill(name=skill.name, description=skill.description)
                if include_descriptions
                else SkillNameOnly(name=skill.name)
            )

        by_type = {"hard": [], "soft": []}
        for category_id, category in catalog.categories.items():
            if category_id in grouped:
                by_type[category.type].append(
                    SkillCategory(name=category.name, skills=grouped[category_id])
                )

        return Roadmap(hard_skills=by_type["hard"], soft_skills=by_type["soft"])

    def get_skills(
        self,
        role_name: str,
        industry: str | None = None,
        seniority_level: str | None = None,
        limit: SkillLimit = 50,
        include_descriptions: bool = False,
    ) -> SkillsResult:
        """Return curated role options with editorial priorities, never candidate claims."""
        catalog = self.catalog
        role = catalog.roles[catalog.resolve("role", role_name)]
        sector = catalog.industries[catalog.resolve("industry", industry)] if industry else None
        level = (
            catalog.levels[catalog.resolve("seniority", seniority_level)]
            if seniority_level
            else None
        )
        if sector and role.id not in sector.role_requirements:
            raise LookupError(
                f"No skills for {role.name} in {sector.name}. "
                "Call list_catalog for supported combinations."
            )

        def eligible(requirement: Requirement) -> bool:
            return level is None or catalog.levels[requirement.minimum_seniority].rank <= level.rank

        def in_role_categories(skill_id: str) -> bool:
            category = response_category(
                skill_id, catalog.categories[catalog.skill_categories[skill_id]].name
            )
            return category in role.response_categories

        requirements = {r.skill_id: r for r in role.requirements}
        selected = {
            option.skill_id: option.priority
            for option in role.skill_options
            if eligible(requirements[option.skill_id]) and in_role_categories(option.skill_id)
        }
        if sector:
            # Industry context supplies optional additions, never promotes role defaults.
            # A role option filtered by seniority must not reappear via industry mappings.
            for requirement in [*sector.role_requirements[role.id], *sector.requirements]:
                skill_id = requirement.skill_id
                if not in_role_categories(skill_id):
                    continue
                if skill_id in requirements and not eligible(requirements[skill_id]):
                    continue
                if eligible(requirement) and catalog.skills[skill_id].type != "soft_skill":
                    selected.setdefault(skill_id, 3)

        model = DescribedRankedSkill if include_descriptions else RankedSkill
        skills = []
        for skill_id in sorted(selected, key=selected.get)[:limit]:
            skill = catalog.skills[skill_id]
            layer = (
                skill.type
                if skill.type in {"implementation_capability", "professional_method"}
                else "core_technology"
            )
            fields = {"description": skill.description} if include_descriptions else {}
            skills.append(
                model(
                    id=skill_id,
                    name=skill.name,
                    type=skill.type,
                    layer=layer,
                    category=catalog.categories[catalog.skill_categories[skill_id]].name,
                    priority=selected[skill_id],
                    technology_ecosystems=skill.technology_ecosystems,
                    technology_family=skill.technology_family,
                    selection_group=skill.selection_group,
                    related_capabilities=[
                        catalog.skills[capability_id].name
                        for capability_id in skill.related_capabilities
                    ],
                    **fields,
                )
            )
        return SkillsResult(
            role=role.name,
            industry=sector.name if sector else None,
            seniority_level=level.name if level else None,
            available_count=len(selected),
            returned_count=len(skills),
            skills=skills,
            category_order=role.response_categories,
        )
