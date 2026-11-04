import json
import sys

import pytest
from mcp import Client, StdioServerParameters

from roadmap_mcp.models import Roadmap
from roadmap_mcp.server import create_server

from .conftest import DATA_DIR, all_categories, all_skills


async def test_real_mcp_discovery_structured_output_and_lookup_errors(catalog):
    async with Client(create_server(catalog)) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
        assert set(tools) == {
            "list_catalog",
            "get_roadmap",
            "get_skills",
            "get_skills_text",
            "list_bullet_catalog",
            "get_bullets",
            "get_bullets_text",
        }
        assert tools["get_roadmap"].output_schema
        assert set(tools["get_roadmap"].output_schema["properties"]) == {
            "hard_skills",
            "soft_skills",
        }
        assert set(tools["get_roadmap"].output_schema["required"]) == {
            "hard_skills",
            "soft_skills",
        }
        assert tools["get_roadmap"].annotations.read_only_hint
        input_schema = tools["get_roadmap"].input_schema
        option = input_schema["properties"]["include_descriptions"]
        assert option["type"] == "boolean"
        assert option["default"] is True
        assert "include_descriptions" not in input_schema["required"]
        result = await client.call_tool(
            "get_roadmap",
            {"role_name": "Backend Engineer", "industry": "Fintech", "seniority_level": "Senior"},
        )
        assert not result.is_error
        roadmap = Roadmap.model_validate(result.structured_content)
        assert set(result.structured_content) == {"hard_skills", "soft_skills"}
        assert all(
            set(category) == {"name", "skills"} and category["skills"]
            for section in result.structured_content.values()
            for category in section
        )
        assert all(
            set(skill) == {"name", "description"}
            for section in result.structured_content.values()
            for category in section
            for skill in category["skills"]
        )
        assert [category.name for category in roadmap.soft_skills] == ["Technical Leadership"]
        assert [skill.name for skill in roadmap.soft_skills[0].skills] == ["Technical leadership"]
        assert len(all_categories(roadmap)) == 14
        assert all_skills(roadmap)[0].name == "Python"
        assert {
            "Java",
            "Spring Boot",
            "PostgreSQL",
            "Redis",
            "Apache Kafka",
            "Docker",
            "Stripe API",
        } <= {skill.name for skill in all_skills(roadmap)}
        invalid = await client.call_tool(
            "get_roadmap",
            {"role_name": "unknown", "industry": "Fintech", "seniority_level": "Senior"},
        )
        assert invalid.is_error
        assert "Supported IDs" in invalid.content[0].text


async def test_mcp_rejects_invalid_arguments(catalog):
    async with Client(create_server(catalog)) as client:
        for args in [
            {"role_name": "Backend Engineer", "industry": "Fintech"},
            {"role_name": "x" * 121, "industry": "Fintech", "seniority_level": "Senior"},
            {"role_name": 123, "industry": "Fintech", "seniority_level": "Senior"},
            *[
                {
                    "role_name": "Backend Engineer",
                    "industry": "Fintech",
                    "seniority_level": "Senior",
                    "include_descriptions": value,
                }
                for value in ["false", 0, None]
            ],
        ]:
            result = await client.call_tool("get_roadmap", args)
            assert result.is_error


@pytest.mark.parametrize("level", ["Junior", "Senior"])
async def test_mcp_omits_descriptions_from_structured_and_text_results(catalog, level):
    async with Client(create_server(catalog)) as client:
        result = await client.call_tool(
            "get_roadmap",
            {
                "role_name": "Backend Engineer",
                "industry": "Fintech",
                "seniority_level": level,
                "include_descriptions": False,
            },
        )
        assert not result.is_error
        payload = result.structured_content
        roadmap = Roadmap.model_validate(payload)
        assert set(payload) == {"hard_skills", "soft_skills"}
        assert all_skills(roadmap)
        assert all(
            set(skill) == {"name"}
            for categories in payload.values()
            for category in categories
            for skill in category["skills"]
        )
        assert json.loads(result.content[0].text) == payload
        if level == "Junior":
            assert payload["soft_skills"] == []
        else:
            assert payload["soft_skills"][0]["skills"] == [{"name": "Technical leadership"}]


async def test_stdio_subprocess_serves_catalog(catalog):
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "roadmap_mcp", "serve", "--transport", "stdio", "--data-dir", str(DATA_DIR)],
    )
    async with Client(parameters) as client:
        result = await client.call_tool("list_catalog")
        assert not result.is_error
        assert {role["id"] for role in result.structured_content["roles"]} == set(catalog.roles)
        assert {industry["id"] for industry in result.structured_content["industries"]} == set(
            catalog.industries
        )
        roadmap = await client.call_tool(
            "get_roadmap",
            {"role_name": "Backend Engineer", "industry": "Fintech", "seniority_level": "Junior"},
        )
        assert not roadmap.is_error
        assert roadmap.structured_content["hard_skills"]
        assert roadmap.structured_content["soft_skills"] == []
        compact = await client.call_tool(
            "get_roadmap",
            {
                "role_name": "Backend Engineer",
                "industry": "Fintech",
                "seniority_level": "Junior",
                "include_descriptions": False,
            },
        )
        assert not compact.is_error
        assert compact.structured_content["hard_skills"][0]["skills"][0] == {"name": "Python"}
        assert compact.structured_content["soft_skills"] == []
        skills = await client.call_tool("get_skills", {"role_name": "AI Engineer"})
        assert not skills.is_error
        assert skills.structured_content["role"] == "AI Engineer"
        assert 30 <= skills.structured_content["returned_count"] <= 50
        assert {s["layer"] for s in skills.structured_content["skills"]} == {
            "core_technology",
            "implementation_capability",
        }
        skills_text = await client.call_tool("get_skills_text", {"role_name": "AI Engineer"})
        assert not skills_text.is_error
        assert skills_text.structured_content is None
        assert skills_text.content[0].text.startswith("AI Engineer\n41 of 41 eligible options\n")
        assert "Core technologies (" in skills_text.content[0].text
        assert "Implementation capabilities (" in skills_text.content[0].text
        bullets = await client.call_tool(
            "get_bullets",
            {
                "role_name": "Backend Engineer",
                "industry": "Fintech",
                "seniority_level": "Senior",
                "count": 5,
            },
        )
        assert not bullets.is_error
        assert bullets.structured_content["available_count"] == 180
        assert bullets.structured_content["returned_count"] == 5
        assert [bullet["industry_id"] for bullet in bullets.structured_content["bullets"][:3]] == [
            "fintech-payments",
            "fintech-payments",
            "fintech-payments",
        ]
        assert all(
            bullet["industry_id"] == "fintech-payments"
            for bullet in bullets.structured_content["bullets"]
        )
        assert all(
            bullet["evidence_to_request"] for bullet in bullets.structured_content["bullets"]
        )
        defaults = await client.call_tool(
            "get_bullets", {"role_name": "Backend Engineer", "count": 1}
        )
        assert not defaults.is_error
        assert defaults.structured_content["industry"] is None
        assert defaults.structured_content["seniority_level"]["id"] == "junior"
        assert defaults.structured_content["available_count"] == 360
        text = await client.call_tool(
            "get_bullets_text", {"role_name": "Backend Engineer", "count": 1}
        )
        assert not text.is_error
        assert text.structured_content is None
        assert "All industries | Junior and above" in text.content[0].text
