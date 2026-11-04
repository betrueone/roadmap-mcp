"""Shared readable skills output for the plain-text MCP tool and local client."""

from textwrap import fill

from roadmap_mcp.models import SkillsResult


def format_skills(result: SkillsResult) -> str:
    title = " | ".join(
        value for value in [result.role, result.industry, result.seniority_level] if value
    )
    lines = [
        title,
        f"{result.returned_count} of {result.available_count} eligible options",
        "Baseline role relevance; select skills using the JD and candidate experience.",
    ]
    if result.industry is None and result.seniority_level is None:
        lines.append("Role catalog across all seniorities; no JD or candidate filtering applied.")
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
