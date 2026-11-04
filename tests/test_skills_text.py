import json
from types import SimpleNamespace

import pytest
from mcp import Client

from roadmap_mcp.models import SkillsResult
from roadmap_mcp.server import create_server
from roadmap_mcp.skills_text import format_skills

from .test_tool import main as run_client


def test_readable_skills_format_includes_layers_metadata_and_descriptions():
    result = SkillsResult.model_validate(
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
    assert format_skills(result) == (
        "Backend Engineer\n"
        "3 of 7 eligible options\n"
        "Baseline role relevance; select skills using the JD and candidate experience.\n"
        "Role catalog across all seniorities; no JD or candidate filtering applied.\n"
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
async def test_text_tool_preserves_structured_selection_and_contract(catalog, args):
    async with Client(create_server(catalog)) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
        tool = tools["get_skills_text"]
        assert tool.output_schema is None
        assert tool.annotations.read_only_hint
        assert tool.input_schema["required"] == ["role_name"]
        assert tool.input_schema["properties"] == tools["get_skills"].input_schema["properties"]
        structured = await client.call_tool("get_skills", args)
        response = await client.call_tool("get_skills_text", args)

    assert not structured.is_error and not response.is_error
    assert response.structured_content is None
    assert len(response.content) == 1 and response.content[0].type == "text"
    text = response.content[0].text
    result = SkillsResult.model_validate(structured.structured_content)
    assert text == format_skills(result)
    title = " | ".join(
        value for value in [result.role, result.industry, result.seniority_level] if value
    )
    assert text.splitlines()[:2] == [
        title,
        f"{result.returned_count} of {result.available_count} eligible options",
    ]
    assert sum(line.startswith("  - ") for line in text.splitlines()) == result.returned_count
    assert ("Role catalog across all seniorities" in text) == (
        result.industry is None and result.seniority_level is None
    )
    assert "[implementation_capability;" not in text
    assert "[professional_method;" not in text
    for skill in result.skills:
        if hasattr(skill, "description"):
            assert skill.description in " ".join(line.strip() for line in text.splitlines())


@pytest.mark.parametrize("mode", ["default", "text", "json"])
async def test_readable_client_output_modes(catalog, service, capsys, mode):
    args = SimpleNamespace(
        url=create_server(catalog),
        role="Backend Engineer",
        industry=None,
        seniority=None,
        limit=2,
        descriptions=True,
        text=mode == "text",
        json=mode == "json",
    )
    await run_client(args)
    output = capsys.readouterr().out
    expected = service.get_skills("Backend Engineer", limit=2, include_descriptions=True)
    if mode == "json":
        assert json.loads(output) == expected.model_dump()
    else:
        assert output == format_skills(expected) + "\n"
