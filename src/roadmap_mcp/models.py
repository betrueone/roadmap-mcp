"""Minimal skill data, selection rules, and public MCP output schemas."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]{0,79}$")]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SkillNameOnly(Model):
    name: Text


class Skill(SkillNameOnly):
    description: Text


class SkillFile(RootModel[dict[Identifier, Skill]]):
    root: dict[Identifier, Skill] = Field(min_length=1)


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


class Role(NamedEntity):
    requirements: list[Requirement] = Field(min_length=1)


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
