import argparse
import asyncio
from textwrap import fill

from mcp import Client


async def main(include_descriptions: bool = True):
    inputs = {
        "role_name": "Backend Engineer",
        "industry": "Fintech",
        "seniority_level": "Senior",
        "include_descriptions": include_descriptions,
    }
    async with Client("http://localhost:8004/mcp") as client:
        result = await client.call_tool("get_roadmap", inputs)
        if result.is_error:
            raise RuntimeError(result.content)

        roadmap = result.structured_content
        title = f"{inputs['seniority_level']} {inputs['role_name']} | {inputs['industry']}"
        print(title)
        print("=" * len(title))

        for section, label in [("hard_skills", "Hard skills"), ("soft_skills", "Soft skills")]:
            categories = roadmap[section]
            count = sum(len(category["skills"]) for category in categories)
            heading = f"{label} ({count})"
            print(f"\n{heading}\n{'-' * len(heading)}")
            if not categories:
                print("  No matching skills.")
            for category in categories:
                print(f"\n{category['name']}")
                for skill in category["skills"]:
                    print(f"  - {skill['name']}")
                    if description := skill.get("description"):
                        print(
                            fill(
                                description,
                                width=100,
                                initial_indent="    ",
                                subsequent_indent="    ",
                            )
                        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print a categorized roadmap from the MCP server.")
    parser.add_argument(
        "--descriptions",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include skill descriptions in the response (default: enabled).",
    )
    args = parser.parse_args()
    asyncio.run(main(include_descriptions=args.descriptions))
