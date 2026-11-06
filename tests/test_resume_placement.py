import json

import pytest
from mcp import Client

from roadmap_mcp.catalog import Catalog, CatalogError
from roadmap_mcp.server import create_server

from .conftest import DATA_DIR, all_skills
from .test_catalog import mutate


def test_industry_source_contains_only_experience_concepts(catalog):
    concepts = json.loads((DATA_DIR / "skills/industries.json").read_text())
    technologies = json.loads((DATA_DIR / "skills/technologies.json").read_text())
    assert len(concepts) == 194
    assert all(skill["resume_section"] == "experience" for skill in concepts.values())
    assert all(skill["type"] == "implementation_capability" for skill in concepts.values())
    assert {"lti", "iso20022", "tmforum-api", "hls", "opc-ua", "reso-web-api", "dcat"} <= (
        technologies.keys()
    )
    assert len(catalog.skills) == 605


@pytest.mark.parametrize(
    "industry, skill_id",
    [
        ("education", "lti"),
        ("banking", "iso20022"),
        ("telecommunications", "tmforum-api"),
        ("media-entertainment", "hls"),
        ("manufacturing", "opc-ua"),
        ("real-estate", "reso-web-api"),
        ("government", "dcat"),
    ],
)
def test_named_industry_standards_remain_skills_without_domain_links(service, industry, skill_id):
    skills = {s.id: s for s in service.get_skills("backend-engineer", industry).skills}
    assert skills[skill_id].layer == "core_technology"
    if skill_id == "dcat":
        assert skills[skill_id].related_capabilities == [
            service.catalog.skills["data-catalogs"].name
        ]
    else:
        assert skills[skill_id].related_capabilities == []


def test_experience_only_concepts_cannot_be_curated_as_skill_options(editable_data):
    def add_concept(role):
        role["requirements"].append({"skill_id": "ledger-modeling"})
        role["skill_options"].append({"skill_id": "ledger-modeling", "priority": 1})

    mutate(editable_data, "roles/backend-engineer.json", add_concept)
    with pytest.raises(CatalogError, match="experience-only skill option ledger-modeling"):
        Catalog(editable_data)


def test_resume_placement_rejects_unknown_values(editable_data):
    mutate(
        editable_data,
        "skills/industries.json",
        lambda skills: skills["ledger-modeling"].update(resume_section="summary"),
    )
    with pytest.raises(CatalogError, match="resume_section"):
        Catalog(editable_data)


async def test_mcp_returns_ledger_concepts_separately_in_every_format(catalog):
    concept_names = {
        skill.name for skill in catalog.skills.values() if skill.resume_section == "experience"
    }
    args = {"role_name": "Backend Engineer", "industry": "Fintech", "seniority_level": "Senior"}
    async with Client(create_server(catalog)) as client:
        summary = await client.call_tool("get_skills", args)
        assert not summary.is_error
        skill_names = {
            name for names in summary.structured_content["skills"].values() for name in names
        }
        assert concept_names.isdisjoint(skill_names)
        assert "Stripe API" in skill_names
        context = {
            concept["name"]: concept for concept in summary.structured_content["industry_context"]
        }
        assert "Financial ledger modeling" in context
        assert "balanced ledger entries" in context["Financial ledger modeling"]["description"]
        for output_format in ["compact", "detailed"]:
            response = await client.call_tool(
                "get_skills_text",
                {**args, "output_format": output_format, "include_descriptions": True},
            )
            assert not response.is_error
            text = response.content[0].text
            if output_format == "compact":
                skills_text, context_text = text.rsplit("\nindustry_context: ", 1)
            else:
                skills_text, context_text = text.split(
                    "\nIndustry context for experience bullets", 1
                )
            assert not any(name in skills_text for name in concept_names)
            assert "Stripe API" in skills_text
            assert "Financial ledger modeling" in context_text
        roadmap = await client.call_tool("get_roadmap", args)
        assert not roadmap.is_error
        assert "Financial ledger modeling" in {
            skill["name"] for skill in roadmap.structured_content["industry_context"]
        }
        assert "Financial ledger modeling" not in {
            skill["name"]
            for category in roadmap.structured_content["hard_skills"]
            for skill in category["skills"]
        }


def test_ledger_concepts_remain_available_for_experience_context(service):
    roadmap = service.get_roadmap("backend-engineer", "fintech", "senior")
    skills = {skill.name: skill for skill in all_skills(roadmap)}
    assert "Financial ledger modeling" in skills
    assert "balanced ledger entries" in skills["Financial ledger modeling"].description


def test_industry_context_is_role_specific_and_independent_of_skills_limit(service):
    backend = service.get_skills("backend-engineer", "fintech", "senior", limit=1)
    frontend = service.get_skills("frontend-engineer", "fintech", "senior", limit=1)
    backend_context = {concept.name for concept in backend.industry_context}
    frontend_context = {concept.name for concept in frontend.industry_context}
    assert "Financial ledger modeling" in backend_context
    assert "Financial ledger modeling" not in frontend_context
    assert "Reliable payment interfaces" in frontend_context
    assert "Reliable payment interfaces" not in backend_context
    assert (
        backend.industry_context
        == service.get_skills("backend-engineer", "fintech", "senior", limit=50).industry_context
    )
    assert service.get_skills("backend-engineer").industry_context == []
    assert backend.returned_count == 1


def test_industry_context_respects_seniority_and_deduplicates_sources(service):
    junior = service.get_skills("backend-engineer", "fintech", "junior")
    senior = service.get_skills("backend-engineer", "fintech", "senior")
    junior_names = {concept.name for concept in junior.industry_context}
    senior_names = {concept.name for concept in senior.industry_context}
    assert junior_names < senior_names
    assert "Financial ledger modeling" not in junior_names
    assert "Financial ledger modeling" in senior_names
    assert len(senior_names) == len(senior.industry_context)
    assert (
        senior.industry_context
        == service.get_roadmap("backend-engineer", "fintech", "senior").industry_context
    )
