"""Shared readable skills output for the plain-text MCP tool and local client."""

from textwrap import fill
from typing import Literal

from roadmap_mcp.models import RankedSkill, SkillsResult

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
    lines = [_title(result)]
    for priority in (1, 2, 3):
        for layer, label in [
            ("core_technology", "technologies"),
            ("implementation_capability", "capabilities"),
            ("professional_method", "methods"),
        ]:
            skills = [
                skill
                for skill in result.skills
                if skill.priority == priority and skill.layer == layer
            ]
            if not skills:
                continue
            heading = f"\nP{priority} {label}:"
            if layer == "core_technology":
                lines.append(heading)
                groups: dict[tuple[str, ...], list[RankedSkill]] = {}
                for skill in skills:
                    key = (
                        ("ecosystem", *skill.technology_ecosystems)
                        if skill.technology_ecosystems
                        else ("category", skill.category)
                    )
                    groups.setdefault(key, []).append(skill)
                for key, entries in groups.items():
                    group = " + ".join(key[1:])
                    lines.append(f"  {group}: {'; '.join(skill.name for skill in entries)}")
            else:
                lines.append(f"{heading} {'; '.join(skill.name for skill in skills)}")
            for skill in skills:
                if description := getattr(skill, "description", None):
                    lines.append(
                        fill(
                            f"{skill.name}: {description}",
                            width=100,
                            initial_indent="    ",
                            subsequent_indent="    ",
                        )
                    )
    return "\n".join(lines)


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
            details = [f"P{skill.priority}", skill.category]
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
    return "\n".join(lines)
