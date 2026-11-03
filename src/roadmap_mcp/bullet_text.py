"""Shared readable output for the plain-text MCP tool and local client."""

from textwrap import fill

from roadmap_mcp.bullet_models import BulletsResult


def format_bullets(result: BulletsResult) -> str:
    industry = result.industry.name if result.industry is not None else "All industries"
    title = f"{result.role.name} | {industry} | {result.seniority_level.name} and above"
    lines = [
        title,
    ]
    if not result.bullets:
        lines.extend(["", "No matching bullets."])
    for index, bullet in enumerate(result.bullets, 1):
        lines.append(f"\n{index}. {bullet.focus} | {bullet.industry_id} | {bullet.seniority}")
        lines.append(fill(bullet.bullet, width=100, initial_indent="   ", subsequent_indent="   "))
    return "\n".join(lines)
