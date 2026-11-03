"""Print resume bullet baselines from a running local MCP server."""

import argparse
import asyncio
import json

from mcp import Client

from roadmap_mcp.bullet_models import BulletsResult
from roadmap_mcp.bullet_text import format_bullets


async def main(
    url: str,
    role: str,
    industry: str | None = None,
    seniority: str | None = None,
    count: int = 5,
    json_output: bool = False,
    text_output: bool = False,
):
    inputs = {
        "role_name": role,
        "count": count,
    }
    if industry is not None:
        inputs["industry"] = industry
    if seniority is not None:
        inputs["seniority_level"] = seniority
    async with Client(url) as client:
        result = await client.call_tool(
            "get_bullets_text" if text_output else "get_bullets", inputs
        )
        if result.is_error:
            raise RuntimeError(result.content)

        if text_output:
            print("\n".join(block.text for block in result.content if block.type == "text"))
            return
        bullets = BulletsResult.model_validate(result.structured_content)
        if json_output:
            print(json.dumps(result.structured_content, indent=2, ensure_ascii=False))
            return

        print(format_bullets(bullets))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default="http://192.168.6.128:8004/mcp",
        help="MCP server URL (default: same local server as tests/test_tool.py).",
    )
    parser.add_argument("--role", default="Backend Engineer", help="Role name, ID, or alias.")
    parser.add_argument("--industry", help="Preferred industry name, ID, or alias (default: all).")
    parser.add_argument(
        "--seniority",
        help="Minimum seniority name, ID, or alias (default: Junior; includes higher).",
    )
    parser.add_argument("--count", type=int, default=5, help="Maximum bullets to return (1–100).")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Print the full JSON response.")
    output.add_argument(
        "--text", action="store_true", help="Call the plain-text get_bullets_text tool."
    )
    args = parser.parse_args()
    if not 1 <= args.count <= 100:
        parser.error("--count must be between 1 and 100")
    asyncio.run(
        main(
            args.url,
            args.role,
            args.industry,
            args.seniority,
            args.count,
            json_output=args.json,
            text_output=args.text,
        )
    )
