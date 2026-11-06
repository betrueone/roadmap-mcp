"""Shared readable skills output for the plain-text MCP tool and local client."""

from textwrap import fill
from typing import Literal

from roadmap_mcp.models import SkillsResponse, SkillsResult
from roadmap_mcp.skill_categories import response_category

SkillsTextFormat = Literal["compact", "detailed"]


def format_skills(result: SkillsResult, output_format: SkillsTextFormat = "compact") -> str:
    if output_format == "compact":
        return _format_compact(result)
    if output_format == "detailed":
        return _format_detailed(result)
    raise ValueError(f"Unknown skills text format: {output_format}")


def _title(result: SkillsResult) -> str:
    return " | ".join(
        value for value in [result.role, result.industry, result.seniority_level] if value
    )


def _format_compact(result: SkillsResult) -> str:
    return format_skills_summary(SkillsResponse.from_result(result))


def format_skills_summary(response: SkillsResponse) -> str:
    categories = ", ".join(response.categories)
    skills = ", ".join(
        f"({name}:{priority})"
        for priority, names in response.skills.model_dump().items()
        for name in names
    )
    context = ", ".join(concept.name for concept in response.industry_context)
    return f"categories: {categories}\nskills: {skills}\nindustry_context: {context}"


def _format_detailed(result: SkillsResult) -> str:
    lines = [_title(result)]
    for layer, label in [
        ("core_technology", "Core technologies"),
        ("implementation_capability", "Implementation capabilities"),
        ("professional_method", "Professional methods"),
    ]:
        skills = [skill for skill in result.skills if skill.layer == layer]
        if not skills:
            continue
        lines.append(f"\n{label} ({len(skills)})")
        for skill in skills:
            details = [f"P{skill.priority - 1}", response_category(skill.id, skill.category)]
            if layer == "core_technology":
                details.insert(0, skill.type)
            lines.append(f"  - {skill.name} [{'; '.join(details)}]")
            if skill.technology_family:
                lines.append(f"    Family: {skill.technology_family}")
            if skill.technology_ecosystems:
                lines.append(f"    Ecosystems: {', '.join(skill.technology_ecosystems)}")
            if skill.selection_group:
                lines.append(f"    Selection group: {skill.selection_group}")
            if skill.related_capabilities:
                lines.append(f"    Related capabilities: {', '.join(skill.related_capabilities)}")
            if description := getattr(skill, "description", None):
                lines.append(
                    fill(description, width=100, initial_indent="    ", subsequent_indent="    ")
                )
    if result.industry_context:
        lines.append(f"\nIndustry context for experience bullets ({len(result.industry_context)})")
        for concept in result.industry_context:
            lines.append(f"  - {concept.name}")
            lines.append(
                fill(
                    concept.description,
                    width=100,
                    initial_indent="    ",
                    subsequent_indent="    ",
                )
            )
    return "\n".join(lines)
