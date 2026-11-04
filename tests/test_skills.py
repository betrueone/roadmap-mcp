import json

import pytest
from mcp import Client

from roadmap_mcp.catalog import Catalog, LookupError
from roadmap_mcp.models import SkillsResult
from roadmap_mcp.server import create_server
from roadmap_mcp.service import RoadmapService

from .test_catalog import mutate


def indexed(result):
    return {skill.id: skill for skill in result.skills}


def test_role_only_ai_catalog_has_both_layers_and_literal_types(service):
    result = service.get_skills("llm engineer")
    assert result.role == "AI Engineer"
    assert result.industry is None and result.seniority_level is None
    assert 30 <= result.returned_count == result.available_count <= 50
    skills = indexed(result)
    assert {s.layer for s in result.skills} == {"core_technology", "implementation_capability"}
    assert {
        key: skills[key].type for key in ["python", "openai-sdk", "langgraph", "pgvector", "rag"]
    } == {
        "python": "language",
        "openai-sdk": "sdk",
        "langgraph": "framework",
        "pgvector": "database_extension",
        "rag": "implementation_capability",
    }
    assert {
        "tool-calling",
        "agent-workflows",
        "structured-generation",
        "model-adaptation",
    } <= skills.keys()
    assert {"technical-leadership", "technical-strategy", "architecture-decisions"}.isdisjoint(
        skills
    )
    assert all("description" not in skill.model_dump() for skill in result.skills)


def test_role_options_are_curated_independently_from_full_roadmap(service):
    skills = indexed(service.get_skills("backend-engineer"))
    assert {"rest-apis", "oauth", "openid", "database-transactions", "postgresql"} <= skills.keys()
    assert {"sqlite", "npm", "orm-data-access", "domain-driven-design"}.isdisjoint(skills)
    assert len(skills) < len(service.catalog.roles["backend-engineer"].requirements)
    assert skills["typescript"].priority == 2
    assert indexed(service.get_skills("AI Engineer"))["typescript"].priority == 2
    assert skills["rest-apis"].layer == "implementation_capability"
    assert skills["oauth"].type == "protocol"


def test_backend_catalog_keeps_alternatives_and_scoped_capability_priorities(service):
    result = service.get_skills("Backend Engineer")
    skills = indexed(result)
    assert result.available_count == result.returned_count == 46
    assert sum(s.layer == "core_technology" for s in result.skills) == 31
    assert sum(s.layer == "implementation_capability" for s in result.skills) == 15
    assert all(
        skills[key].priority == 2
        for key in [
            "python",
            "java",
            "go",
            "javascript",
            "typescript",
            "nodejs",
            "postgresql",
            "redis",
            "containers",
            "database-transactions",
            "authorization",
            "database-indexing",
            "service-resilience",
        ]
    )
    assert all(
        skills[key].priority == 1
        for key in [
            "rest-apis",
            "sql-modeling",
            "authentication",
            "unit-testing",
            "integration-testing",
        ]
    )
    assert (
        skills["python"].technology_ecosystems
        == skills["fastapi"].technology_ecosystems
        == ["Python"]
    )
    assert (
        skills["django"].technology_ecosystems
        == skills["pytest"].technology_ecosystems
        == ["Python"]
    )
    assert (
        skills["java"].technology_ecosystems
        == skills["spring-boot"].technology_ecosystems
        == ["Java / JVM"]
    )
    for key in ["javascript", "typescript", "nodejs", "expressjs", "nestjs"]:
        assert skills[key].technology_ecosystems == ["JavaScript / TypeScript"]
    assert skills["go"].technology_ecosystems == ["Go"]
    assert (
        skills["postgresql"].technology_ecosystems
        == skills["rest-apis"].technology_ecosystems
        == []
    )


def test_specialized_technology_types_are_shared_across_roles(service):
    expected = {
        "nodejs": "runtime",
        "apache-kafka": "event_streaming_platform",
        "rabbitmq": "message_broker",
        "graphql": "api_query_language",
        **dict.fromkeys(["pytest", "junit", "jest", "vitest", "xctest"], "test_framework"),
        **dict.fromkeys(["github-actions", "gitlab-ci", "jenkins"], "ci_cd_platform"),
    }
    seen = set()
    for role in service.catalog.roles:
        for skill in service.get_skills(role).skills:
            if skill.id in expected:
                assert skill.type == expected[skill.id]
                assert skill.layer == "core_technology"
                seen.add(skill.id)
    assert seen == expected.keys()


def test_ecosystems_are_optional_nonexclusive_hints(editable_data):
    mutate(
        editable_data,
        "skills/technologies.json",
        lambda d: d["python"].pop("technology_ecosystems"),
    )
    mutate(
        editable_data,
        "skills/technologies.json",
        lambda d: d["playwright"].update(
            technology_ecosystems=["Python", "JavaScript / TypeScript"]
        ),
    )
    service = RoadmapService(Catalog(editable_data))
    assert indexed(service.get_skills("Backend Engineer"))["python"].technology_ecosystems == []
    qa = indexed(service.get_skills("QA Engineer"))
    assert qa["playwright"].technology_ecosystems == ["Python", "JavaScript / TypeScript"]
    assert {"playwright", "cypress", "selenium"} <= qa.keys()


def test_ai_capability_priorities_keep_specific_core_and_broad_supporting_options(service):
    result = service.get_skills("AI Engineer")
    skills = indexed(result)
    assert len(skills) == 41
    assert {
        s.id for s in result.skills if s.layer == "implementation_capability" and s.priority == 1
    } == {"rag", "tool-calling", "structured-generation", "llm-evaluation"}
    assert all(
        skills[key].priority == 2
        for key in [
            "embeddings",
            "vector-search",
            "agent-workflows",
            "document-ingestion",
            "prompt-engineering",
        ]
    )
    assert all(
        skills[key].priority == 3
        for key in [
            "unit-testing",
            "integration-testing",
            "responsible-ml",
            "cost-optimization",
            "privacy-engineering",
        ]
    )


def test_technology_families_preserve_related_options_without_collapsing_them(service):
    skills = indexed(service.get_skills("AI Engineer"))
    for key in ["pgvector", "qdrant", "pinecone", "chroma", "faiss"]:
        assert skills[key].technology_family == "Vector Retrieval"
        assert skills[key].related_capabilities == [
            "Retrieval-Augmented Generation (RAG)",
            "Vector search",
        ]
    # Family membership does not erase implementation differences or imply substitutes.
    assert skills["faiss"].type == "library"
    assert skills["pgvector"].type == "database_extension"
    assert (
        len({skills[key].technology_family for key in ["langchain", "langgraph", "llama-index"]})
        == 3
    )
    assert skills["langgraph"].related_capabilities == ["Agent workflows", "Function calling"]
    assert skills["rag"].technology_family is None
    assert skills["rag"].related_capabilities == []
    assert skills["python"].related_capabilities == []


def test_selection_groups_distinguish_architecture_positions_without_deduplication(service):
    skills = indexed(service.get_skills("AI Engineer"))
    assert all(
        skills[key].selection_group == "Vector Storage"
        for key in ["pgvector", "qdrant", "pinecone", "chroma"]
    )
    assert skills["faiss"].selection_group == "Vector Index"
    assert skills["postgresql"].selection_group == "Relational Storage"
    # Complementary storage and extension remain together; comparison hints never drop options.
    assert len(skills) == 41
    assert skills["python"].selection_group is None
    assert skills["rag"].selection_group is None
    assert skills["langchain"].selection_group is None
    assert skills["langgraph"].selection_group is None


def test_selection_group_can_be_omitted_from_source(editable_data):
    mutate(
        editable_data,
        "skills/technologies.json",
        lambda d: d["pgvector"].pop("selection_group"),
    )
    skills = indexed(RoadmapService(Catalog(editable_data)).get_skills("AI Engineer"))
    assert skills["pgvector"].selection_group is None
    assert skills["pgvector"].technology_family == "Vector Retrieval"


def test_capability_links_resolve_beyond_the_filtered_ai_catalog(service, catalog):
    skills = indexed(service.get_skills("AI Engineer"))
    outside = {
        capability_name
        for skill in skills.values()
        for capability_name in skill.related_capabilities
        if capability_name not in {entry.name for entry in skills.values()}
    }
    assert {
        "Schema validation",
        "RESTful APIs",
        "Reproducible builds and artifact promotion",
        "Relational schema design",
        "Distributed tracing",
    } <= outside
    capability_names = {
        skill.name for skill in catalog.skills.values() if skill.type == "implementation_capability"
    }
    assert outside <= capability_names
    assert skills["redis"].related_capabilities == [
        "Cache invalidation and expiration",
        "Session and token authentication",
        "Message acknowledgments and dead-letter queues",
    ]
    assert skills["fastapi"].related_capabilities == [
        "RESTful APIs",
        "Schema validation",
        "OpenAPI specifications",
    ]
    assert skills["pydantic"].related_capabilities == ["Schema validation", "Structured outputs"]
    assert skills["opentelemetry"].related_capabilities == [
        "Distributed tracing",
        "Application metrics instrumentation",
    ]
    assert skills["ragas"].related_capabilities == [
        "LLM evaluation",
        "Retrieval-Augmented Generation (RAG)",
    ]


def test_related_capability_names_follow_canonical_catalog_names(editable_data):
    mutate(
        editable_data,
        "skills/backend.json",
        lambda d: d["sql-modeling"].update(name="Relational schema modeling"),
    )
    service = RoadmapService(Catalog(editable_data))
    skills = indexed(service.get_skills("Data Engineer", limit=2))
    assert skills["sql"].related_capabilities == [
        "SQL window functions and CTEs",
        "Relational schema modeling",
    ]
    assert "sql-modeling" not in skills
    assert service.catalog.skills["sql"].related_capabilities == ["advanced-sql", "sql-modeling"]


def test_priority_remains_role_specific_baseline_without_jd_ranking(service):
    ai = indexed(service.get_skills("AI Engineer"))
    ml = indexed(service.get_skills("ML Engineer"))
    assert ai["fastapi"].priority == ml["fastapi"].priority == 2
    assert ai["unit-testing"].priority == 3 and ml["unit-testing"].priority == 2
    assert ai["model-serving"].priority == 3 and ml["model-serving"].priority == 1
    assert all("jd_priority" not in skill.model_dump() for skill in [*ai.values(), *ml.values()])


def test_metadata_links_can_reference_skills_outside_filtered_response(service):
    result = service.get_skills("Data Engineer", seniority_level="Mid-level", limit=2)
    skills = indexed(result)
    assert "sql" in skills
    assert "SQL window functions and CTEs" in skills["sql"].related_capabilities
    assert "advanced-sql" not in skills
    assert result.returned_count == 2
    # Family metadata also survives industry selection, limits, and description modes.
    industrial = indexed(service.get_skills("Backend Engineer", "Manufacturing"))
    assert industrial["opc-ua"].technology_family == "Industrial Interoperability"
    assert industrial["opc-ua"].related_capabilities == ["Production system integration"]


def test_industry_additions_do_not_promote_role_defaults(service, editable_data):
    # An overlapping industry reference must preserve the role's priority.
    mutate(
        editable_data,
        "industries/saas.json",
        lambda d: d["requirements"].append({"skill_id": "rag"}),
    )
    contextual = RoadmapService(Catalog(editable_data)).get_skills("AI Engineer", "SaaS")
    baseline = indexed(service.get_skills("AI Engineer"))
    skills = indexed(contextual)
    assert skills["rag"].priority == baseline["rag"].priority == 1
    assert "saas-knowledge-retrieval" in skills
    assert skills["saas-knowledge-retrieval"].priority == 3
    assert all(skills[key].priority == value.priority for key, value in baseline.items())
    assert contextual.industry == "SaaS"


def test_priority_order_limit_and_description_modes(service):
    full = service.get_skills("Data Engineer", "Fintech")
    compact = service.get_skills("Data Engineer", "Fintech", limit=7)
    described = service.get_skills("Data Engineer", "Fintech", limit=7, include_descriptions=True)
    assert compact.skills == full.skills[:7]
    assert compact.returned_count == 7
    assert compact.available_count == described.available_count == full.available_count
    assert compact.available_count > full.returned_count == 50
    assert [s.priority for s in full.skills] == sorted(s.priority for s in full.skills)
    assert compact.model_dump() == {
        **described.model_dump(),
        "skills": [s.model_dump(exclude={"description"}) for s in described.skills],
    }
    assert all(s.description for s in described.skills)
    assert service.get_skills("Data Engineer", "Fintech") == full


def test_seniority_filters_do_not_change_role_priorities_or_reintroduce_skills(
    service, editable_data
):
    mutate(
        editable_data,
        "industries/saas.json",
        lambda d: d["requirements"].append({"skill_id": "rag", "minimum_seniority": "junior"}),
    )
    customized = RoadmapService(Catalog(editable_data))
    junior = customized.get_skills("AI Engineer", "SaaS", "Junior")
    senior = customized.get_skills("AI Engineer", "SaaS", "Senior")
    assert junior.seniority_level == "Junior"
    assert "rag" not in indexed(junior)
    assert "rag" in indexed(senior)
    assert "agent-workflows" not in indexed(junior)
    assert "agent-workflows" in indexed(senior)
    assert all(s.priority == indexed(senior)[s.id].priority for s in junior.skills)
    assert indexed(service.get_skills("AI Engineer"))["model-adaptation"].priority == 3


def test_every_role_and_combination_has_valid_bounded_skill_options(service, catalog):
    for role in catalog.roles.values():
        baseline = service.get_skills(role.id)
        # Nonengineering methods have smaller inventories; don't pad them to a quota.
        if role.id not in {"ux-designer", "product-manager", "engineering-manager"}:
            assert 30 <= baseline.returned_count <= 50
        for industry in catalog.industries.values():
            for level in catalog.levels.values():
                result = service.get_skills(role.id, industry.id, level.id)
                assert 0 < result.returned_count == len(result.skills) <= 50
                assert result.available_count >= result.returned_count
                assert len(indexed(result)) == len(result.skills)
                assert all(s.type != "soft_skill" for s in result.skills)
                assert all(s.category for s in result.skills)
                assert {s.id for s in result.skills} <= catalog.skills.keys()
                for skill in result.skills:
                    stored = catalog.skills[skill.id]
                    assert skill.technology_family == stored.technology_family
                    assert skill.selection_group == stored.selection_group
                    assert skill.technology_ecosystems == stored.technology_ecosystems
                    assert skill.related_capabilities == [
                        catalog.skills[key].name for key in stored.related_capabilities
                    ]
                    assert bool(skill.technology_family) == (skill.layer == "core_technology")


def test_categories_and_methods_vary_by_role(service):
    frontend = service.get_skills("Frontend Engineer")
    data = service.get_skills("Data Engineer")
    designer = service.get_skills("UX Designer")
    assert "Frontend Frameworks & UI" in {s.category for s in frontend.skills}
    assert "Frontend Frameworks & UI" not in {s.category for s in data.skills}
    assert any(s.type == "professional_method" for s in designer.skills)
    assert "python" not in indexed(designer)


@pytest.mark.parametrize(
    "args",
    [
        {"role_name": "unknown"},
        {"role_name": "AI Engineer", "industry": "unknown"},
        {"role_name": "AI Engineer", "seniority_level": "unknown"},
    ],
)
def test_unknown_inputs_error_without_fallback(service, args):
    with pytest.raises(LookupError, match="Supported IDs"):
        service.get_skills(**args)


def test_unsupported_industry_combination_errors(editable_data):
    mutate(
        editable_data, "industries/saas.json", lambda d: d["role_requirements"].pop("ai-engineer")
    )
    service = RoadmapService(Catalog(editable_data))
    with pytest.raises(LookupError, match="No skills"):
        service.get_skills("AI Engineer", "SaaS")


async def test_mcp_skills_discovery_and_description_modes(catalog):
    async with Client(create_server(catalog)) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
        tool = tools["get_skills"]
        assert tool.annotations.read_only_hint
        assert tool.input_schema["required"] == ["role_name"]
        assert tool.input_schema["properties"]["include_descriptions"]["default"] is False
        assert tool.output_schema["properties"]["skills"]
        for descriptions in [False, True]:
            response = await client.call_tool(
                "get_skills", {"role_name": "AI Engineer", "include_descriptions": descriptions}
            )
            assert not response.is_error
            result = SkillsResult.model_validate(response.structured_content)
            assert result.role == "AI Engineer"
            assert 30 <= result.returned_count <= 50
            assert all(
                ("description" in s) == descriptions for s in response.structured_content["skills"]
            )
            skills = {s["id"]: s for s in response.structured_content["skills"]}
            assert skills["pgvector"]["technology_family"] == "Vector Retrieval"
            assert skills["pgvector"]["selection_group"] == "Vector Storage"
            assert skills["pgvector"]["related_capabilities"] == [
                "Retrieval-Augmented Generation (RAG)",
                "Vector search",
            ]
            assert skills["rag"]["technology_family"] is None
            assert skills["rag"]["selection_group"] is None
            assert skills["python"]["selection_group"] is None
            assert skills["python"]["technology_ecosystems"] == ["Python"]
            assert skills["fastapi"]["technology_ecosystems"] == ["Python"]
            assert skills["rag"]["technology_ecosystems"] == []
            assert skills["rag"]["related_capabilities"] == []
            assert json.loads(response.content[0].text) == response.structured_content


@pytest.mark.parametrize(
    "args",
    [
        {},
        {"role_name": "unknown"},
        {"role_name": "AI Engineer", "industry": "unknown"},
        {"role_name": "AI Engineer", "seniority_level": "unknown"},
        *[{"role_name": "AI Engineer", "limit": limit} for limit in [0, 51, True, "5", None]],
        *[
            {"role_name": "AI Engineer", "include_descriptions": value}
            for value in ["false", 0, None]
        ],
    ],
)
@pytest.mark.parametrize("tool_name", ["get_skills", "get_skills_text"])
async def test_mcp_rejects_invalid_skills_arguments(catalog, args, tool_name):
    async with Client(create_server(catalog)) as client:
        result = await client.call_tool(tool_name, args)
        assert result.is_error
