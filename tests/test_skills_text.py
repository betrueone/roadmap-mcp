import json
import re
from collections import Counter
from types import SimpleNamespace

import pytest
from mcp import Client

from roadmap_mcp.models import SkillsResult
from roadmap_mcp.server import create_server
from roadmap_mcp.skills_text import format_skills

from .test_tool import main as run_client


@pytest.fixture
def example_skills():
    return SkillsResult.model_validate(
        {
            "role": "Backend Engineer",
            "industry": None,
            "seniority_level": None,
            "available_count": 7,
            "returned_count": 3,
            "skills": [
                {
                    "id": "rest-apis",
                    "name": "RESTful APIs",
                    "type": "implementation_capability",
                    "layer": "implementation_capability",
                    "category": "APIs & Integration",
                    "priority": 1,
                },
                {
                    "id": "fastapi",
                    "name": "FastAPI",
                    "type": "framework",
                    "layer": "core_technology",
                    "category": "Backend Frameworks & Runtimes",
                    "priority": 2,
                    "technology_family": "Backend Frameworks",
                    "technology_ecosystems": ["Python"],
                    "selection_group": "Backend API Framework",
                    "related_capabilities": ["RESTful APIs", "Schema validation"],
                    "description": "Build typed APIs.",
                },
                {
                    "id": "roadmapping",
                    "name": "Product roadmapping",
                    "type": "professional_method",
                    "layer": "professional_method",
                    "category": "Product Management",
                    "priority": 3,
                },
            ],
        }
    )


def test_detailed_format_preserves_metadata_and_minimal_header(example_skills):
    assert format_skills(example_skills, "detailed") == (
        "Backend Engineer\n"
        "\nCore technologies (1)\n"
        "  - FastAPI [framework; P2; Backend Frameworks & Runtimes]\n"
        "    Family: Backend Frameworks\n"
        "    Ecosystems: Python\n"
        "    Selection group: Backend API Framework\n"
        "    Related capabilities: RESTful APIs, Schema validation\n"
        "    Build typed APIs.\n"
        "\nImplementation capabilities (1)\n"
        "  - RESTful APIs [P1; APIs & Integration]\n"
        "\nProfessional methods (1)\n"
        "  - Product roadmapping [P3; Product Management]"
    )


def test_compact_format_groups_priorities_and_layers(example_skills):
    assert format_skills(example_skills) == (
        "Backend Engineer\n"
        "\nP1 capabilities: RESTful APIs\n"
        "\nP2 technologies:\n"
        "  Python: FastAPI\n"
        "    FastAPI: Build typed APIs.\n"
        "\nP3 methods: Product roadmapping"
    )


def test_compact_keeps_all_ecosystem_associations_without_duplicate_skills(example_skills):
    skill = example_skills.skills[1].model_copy(
        update={"technology_ecosystems": ["Python", "JavaScript / TypeScript"]}
    )
    result = example_skills.model_copy(update={"skills": [skill]})
    text = format_skills(result)
    assert "  Python + JavaScript / TypeScript: FastAPI\n" in text


def test_compact_preserves_every_skill_priority_and_layer_across_roles(service):
    layer_labels = {
        "technologies": "core_technology",
        "capabilities": "implementation_capability",
        "methods": "professional_method",
    }
    for role in service.catalog.roles:
        result = service.get_skills(role)
        entries = []
        for line in format_skills(result).splitlines()[1:]:
            if not line:
                continue
            if heading := re.fullmatch(r"P([123]) (technologies|capabilities|methods):(.*)", line):
                priority = int(heading[1])
                layer = layer_labels[heading[2]]
                names = heading[3].strip()
            else:
                assert line.startswith("  ") and layer == "core_technology"
                names = line.split(": ", 1)[1]
            if names:
                entries.extend((priority, layer, name) for name in names.split("; "))
        assert Counter(entries) == Counter(
            (skill.priority, skill.layer, skill.name) for skill in result.skills
        ), role


@pytest.mark.parametrize(
    "args",
    [
        {"role_name": "Backend Engineer"},
        {"role_name": "backend-engineer", "industry": None, "seniority_level": None},
        {
            "role_name": "Backend Engineer",
            "industry": "Fintech",
            "seniority_level": "Junior",
            "limit": 12,
            "include_descriptions": True,
        },
        {"role_name": "UX Designer", "seniority_level": "Senior"},
        {"role_name": "Data Engineer", "limit": 1},
    ],
)
@pytest.mark.parametrize("output_format", ["compact", "detailed"])
async def test_text_tool_preserves_structured_selection_and_contract(catalog, args, output_format):
    async with Client(create_server(catalog)) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
        tool = tools["get_skills_text"]
        assert tool.output_schema is None
        assert tool.annotations.read_only_hint
        assert tool.input_schema["required"] == ["role_name"]
        properties = tool.input_schema["properties"].copy()
        format_property = properties.pop("output_format")
        assert format_property["default"] == "compact"
        assert format_property["enum"] == ["compact", "detailed"]
        assert properties == tools["get_skills"].input_schema["properties"]
        structured = await client.call_tool("get_skills", args)
        response = await client.call_tool(
            "get_skills_text", {**args, "output_format": output_format}
        )

    assert not structured.is_error and not response.is_error
    assert response.structured_content is None
    assert len(response.content) == 1 and response.content[0].type == "text"
    text = response.content[0].text
    result = SkillsResult.model_validate(structured.structured_content)
    assert text == format_skills(result, output_format)
    title = " | ".join(
        value for value in [result.role, result.industry, result.seniority_level] if value
    )
    assert text.splitlines()[0] == title
    assert "eligible options" not in text
    assert "Role catalog across all seniorities" not in text
    if output_format == "detailed":
        assert sum(line.startswith("  - ") for line in text.splitlines()) == result.returned_count
    assert "[implementation_capability;" not in text
    assert "[professional_method;" not in text
    for skill in result.skills:
        if hasattr(skill, "description"):
            assert skill.description in " ".join(line.strip() for line in text.splitlines())


@pytest.mark.parametrize("mode", ["default", "text", "json"])
@pytest.mark.parametrize("output_format", ["compact", "detailed"])
async def test_readable_client_output_modes(catalog, service, capsys, mode, output_format):
    args = SimpleNamespace(
        url=create_server(catalog),
        role="Backend Engineer",
        industry=None,
        seniority=None,
        limit=2,
        descriptions=True,
        output_format=output_format,
        text=mode == "text",
        json=mode == "json",
    )
    await run_client(args)
    output = capsys.readouterr().out
    expected = service.get_skills("Backend Engineer", limit=2, include_descriptions=True)
    if mode == "json":
        assert json.loads(output) == expected.model_dump()
    else:
        assert output == format_skills(expected, output_format) + "\n"


@pytest.mark.parametrize("output_format", ["unknown", "COMPACT", "", None, True, 1])
async def test_text_tool_rejects_invalid_output_format(catalog, output_format):
    async with Client(create_server(catalog)) as client:
        result = await client.call_tool(
            "get_skills_text", {"role_name": "Backend Engineer", "output_format": output_format}
        )
    assert result.is_error
