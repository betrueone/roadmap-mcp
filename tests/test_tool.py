"""Readable client for the curated get_skills MCP tool."""

import argparse
import asyncio
import json

from mcp import Client

from roadmap_mcp.models import SkillsResult
from roadmap_mcp.skills_text import format_skills


async def main(args):
    inputs = {
        "role_name": args.role,
        "industry": args.industry,
        "seniority_level": args.seniority,
        "limit": args.limit,
        "include_descriptions": args.descriptions,
    }
    if args.text:
        inputs["output_format"] = args.output_format
    async with Client(args.url) as client:
        response = await client.call_tool("get_skills_text" if args.text else "get_skills", inputs)
        if response.is_error:
            raise RuntimeError(response.content)
        if args.text:
            print("\n".join(block.text for block in response.content if block.type == "text"))
            return
        result = response.structured_content
        if args.json:
            print(json.dumps(result, indent=2))
            return
        print(format_skills(SkillsResult.model_validate(result), args.output_format))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8004/mcp")
    parser.add_argument("--role", default="Backend Engineer")
    parser.add_argument("--industry")
    parser.add_argument("--seniority")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--descriptions", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument(
        "--output-format",
        choices=["compact", "detailed"],
        default="compact",
        help="Readable output format (default: compact); also applies to --text.",
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Print the full JSON response.")
    output.add_argument(
        "--text", action="store_true", help="Call the plain-text get_skills_text tool."
    )
    asyncio.run(main(parser.parse_args()))
