"""Minimal skill data, selection rules, and public MCP output schemas."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, StringConstraints

from roadmap_mcp.skill_categories import response_category

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]{0,79}$")]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SkillNameOnly(Model):
    name: Text


class Skill(SkillNameOnly):
    description: Text


SkillType = Literal[
    "language",
    "framework",
    "sdk",
    "library",
    "database",
    "database_extension",
    "runtime",
    "event_streaming_platform",
    "message_broker",
    "test_framework",
    "ci_cd_platform",
    "api_query_language",
    "api",
    "operating_system",
    "cloud_platform",
    "cloud_service",
    "infrastructure",
    "tool",
    "protocol",
    "standard",
    "implementation_capability",
    "professional_method",
    "soft_skill",
]
Priority = Annotated[int, Field(strict=True, ge=1, le=3)]
SkillLimit = Annotated[int, Field(strict=True, ge=1, le=50)]


class TechnologyMetadata(Model):
    technology_ecosystems: list[Text] = Field(
        default_factory=list,
        description=(
            "Curated language/runtime ecosystem names for coherent stack selection. "
            "Nonexhaustive hints, not dependencies or a single-stack restriction; "
            "empty means no curated ecosystem association."
        ),
    )
    technology_family: Text | None = Field(
        default=None, description="Readable name for a technology's engineering purpose."
    )
    selection_group: Text | None = Field(
        default=None,
        description=(
            "Optional readable group name for technologies filling similar "
            "architectural positions. "
            "Not a one-per-group rule or proof of interchangeability."
        ),
    )


class StoredSkill(Skill, TechnologyMetadata):
    type: SkillType
    resume_section: Literal["skills", "experience"] = Field(
        default="skills",
        description=(
            "Resume placement: experience-only concepts are excluded from skill groups "
            "and capability links, and returned separately as industry context."
        ),
    )
    # Canonical references remain internal; responses resolve them to catalog names.
    related_capabilities: list[Identifier] = Field(default_factory=list)


class SkillFile(RootModel[dict[Identifier, StoredSkill]]):
    root: dict[Identifier, StoredSkill] = Field(min_length=1)


class Category(Model):
    name: Text
    type: Literal["hard", "soft"]
    skill_ids: list[Identifier] = Field(min_length=1)


class CategoryFile(RootModel[dict[Identifier, Category]]):
    root: dict[Identifier, Category] = Field(min_length=1)


class Requirement(Model):
    skill_id: Identifier
    minimum_seniority: Identifier = "junior"


class NamedEntity(Model):
    id: Identifier
    name: Text
    aliases: list[Text] = Field(default_factory=list)


class SkillOption(Model):
    skill_id: Identifier
    priority: Priority


class Role(NamedEntity):
    response_categories: list[Text] = Field(
        min_length=1,
        description="Ordered response categories for this role and its industry options.",
    )
    required_categories: list[Text] = Field(
        min_length=1,
        description=(
            "Categories requiring curated baseline coverage across the full seniority inventory; "
            "filtered responses and candidate skill selections need not include every category."
        ),
    )
    requirements: list[Requirement] = Field(min_length=1)
    # A deliberately curated subset, separate from the cumulative roadmap inventory.
    skill_options: list[SkillOption] = Field(min_length=1, max_length=50)


class Industry(NamedEntity):
    requirements: list[Requirement] = Field(default_factory=list)
    # Missing roles are unsupported; an empty list explicitly supports a combination.
    role_requirements: dict[Identifier, list[Requirement]] = Field(min_length=1)


class Seniority(NamedEntity):
    rank: int = Field(ge=0, le=100)


class SeniorityFile(Model):
    levels: list[Seniority] = Field(min_length=1)


class CatalogEntry(Model):
    id: str
    name: str
    aliases: list[str]


class Coverage(Model):
    role_id: str
    industry_ids: list[str]


class CatalogResult(Model):
    roles: list[CatalogEntry]
    industries: list[CatalogEntry]
    seniority_levels: list[CatalogEntry]
    coverage: list[Coverage]


class SkillCategory(Model):
    name: Text
    skills: list[Skill | SkillNameOnly] = Field(min_length=1)


class Roadmap(Model):
    hard_skills: list[SkillCategory]
    soft_skills: list[SkillCategory]
    industry_context: list[Skill | SkillNameOnly] = Field(
        default_factory=list,
        description="Industry concepts for evidenced experience bullets, separate from skills.",
    )


class RankedSkill(TechnologyMetadata):
    id: Identifier
    name: Text
    type: SkillType
    layer: Literal["core_technology", "implementation_capability", "professional_method"]
    category: Text
    priority: Priority
    related_capabilities: list[Text] = Field(
        default_factory=list,
        description="Canonical implementation-capability names from the full catalog, not IDs.",
    )


class DescribedRankedSkill(RankedSkill):
    description: Text


class SkillsResult(Model):
    role: Text
    industry: Text | None
    seniority_level: Text | None
    available_count: int = Field(ge=0)
    returned_count: int = Field(ge=0, le=50)
    skills: list[DescribedRankedSkill | RankedSkill] = Field(max_length=50)
    category_order: list[Text] = Field(default_factory=list)
    industry_context: list[Skill] = Field(default_factory=list)


class SkillPriorities(Model):
    P0: list[Text]
    P1: list[Text]
    P2: list[Text]


class SkillsResponse(Model):
    role: Text
    industry: Text | None
    seniority: Text | None
    categories: list[Text]
    skills: SkillPriorities
    industry_context: list[Skill] = Field(
        default_factory=list,
        description=(
            "Role- and seniority-filtered industry concepts with descriptions for evidenced "
            "experience bullets. Separate from skills, priorities, category coverage, and limit; "
            "empty when industry is omitted."
        ),
    )

    @classmethod
    def from_result(cls, result: SkillsResult) -> "SkillsResponse":
        selected_categories: dict[str, None] = {}
        priorities: dict[str, list[str]] = {"P0": [], "P1": [], "P2": []}
        for skill in result.skills:
            category = response_category(skill.id, skill.category)
            selected_categories[category] = None
            priorities[f"P{skill.priority - 1}"].append(skill.name)
        return cls(
            role=result.role,
            industry=result.industry,
            seniority=result.seniority_level,
            categories=[
                name
                for name in (result.category_order or selected_categories)
                if name in selected_categories
            ],
            skills=SkillPriorities(**priorities),
            industry_context=result.industry_context,
        )
