"""Cross-role regression checks for the non-bullet datasource review."""

import pytest

from roadmap_mcp.catalog import Catalog, CatalogError

from .conftest import all_skills
from .test_catalog import mutate
from .test_skills import indexed


def test_distinct_technology_identities_survive_discovery(service):
    expected = {
        "react": "library",
        "rpc-contracts": "framework",
        "databricks-delta-lake": "framework",
        "opentelemetry": "framework",
        "core-data": "framework",
        "combine": "framework",
        "linux-cli": "operating_system",
        "aws": "cloud_platform",
        "firebase": "cloud_platform",
        "aws-iam": "cloud_service",
        "aws-rds": "cloud_service",
        "azure-data-factory": "cloud_service",
        "stripe-api": "api",
        "shopify-admin-api": "api",
        "hls": "protocol",
        "cypress": "test_framework",
        "locust": "test_framework",
    }
    seen = set()
    for role in service.catalog.roles:
        for industry in [None, "fintech", "e-commerce", "media-entertainment"]:
            for skill in service.get_skills(role, industry).skills:
                if skill.id in expected:
                    assert skill.type == expected[skill.id]
                    assert skill.layer == "core_technology"
                    seen.add(skill.id)
    assert seen == expected.keys()


@pytest.mark.parametrize(
    "role, alternatives, core",
    [
        ("cloud-engineer", ["aws", "azure", "google-cloud"], "infrastructure-as-code"),
        ("mobile-engineer", ["dart", "react-native", "flutter", "typescript"], "mobile-lifecycle"),
        ("qa-engineer", ["python", "typescript", "pytest", "playwright"], "test-design"),
        ("platform-engineer", ["python", "go", "github-actions"], "platform-api-design"),
        ("ai-engineer", ["openai-sdk", "fastapi", "pgvector"], "llm-evaluation"),
        ("product-manager", ["jira", "linear"], "product-prioritization"),
    ],
)
def test_generic_roles_rank_alternatives_below_core_work(service, role, alternatives, core):
    skills = indexed(service.get_skills(role))
    assert skills[core].priority == 1
    assert all(skills[key].priority == 2 for key in alternatives)


@pytest.mark.parametrize(
    "role, basics, advanced",
    [
        ("backend-engineer", {"typescript", "fastapi", "pytest"}, "distributed-transactions"),
        ("frontend-engineer", {"typescript", "react", "vitest"}, "server-rendering"),
        ("full-stack-engineer", {"react", "authentication", "sql-modeling"}, "multi-tenancy"),
        ("android-developer", {"jetpack-compose", "junit"}, "offline-synchronization"),
        ("ios-developer", {"swiftui", "xctest"}, "offline-synchronization"),
        ("ai-engineer", {"openai-sdk", "pydantic", "pytest"}, "agent-workflows"),
        ("data-scientist", {"scikit-learn", "model-evaluation"}, "causal-inference"),
        ("qa-engineer", {"python", "pytest", "playwright"}, "test-automation-architecture"),
    ],
)
def test_junior_options_allow_basic_implementation_without_advanced_ownership(
    service, role, basics, advanced
):
    junior = indexed(service.get_skills(role, seniority_level="junior"))
    senior = indexed(service.get_skills(role, seniority_level="senior"))
    assert basics <= junior.keys()
    assert advanced not in junior and advanced in senior
    assert all(skill.priority == senior[key].priority for key, skill in junior.items())


def test_backend_language_alternatives_do_not_depend_on_industry(service):
    for role in ["backend-engineer", "full-stack-engineer"]:
        for industry in [None, *service.catalog.industries]:
            skills = indexed(service.get_skills(role, industry))
            assert {"php", "ruby"} <= skills.keys()
            assert skills["php"].priority == skills["ruby"].priority == 3


def test_ui_payment_roles_keep_client_flows_without_server_api_operations(service):
    for role in ["frontend-engineer", "android-developer", "ios-developer", "mobile-engineer"]:
        roadmap = service.get_roadmap(role, "fintech", "senior")
        names = {skill.name for skill in all_skills(roadmap)}
        assert "Stripe API" not in names
        assert {"Reliable payment interfaces", "Payment authentication interfaces"} <= names
    backend = service.get_roadmap("backend-engineer", "fintech", "senior")
    assert "Stripe API" in {skill.name for skill in all_skills(backend)}


def test_domain_access_context_stays_in_mid_level_roadmaps(service):
    for industry, control in [
        ("saas", "tenant-isolation"),
        ("banking", "banking-authorization"),
        ("education", "student-data-protection"),
        ("government", "public-information-controls"),
    ]:
        skills = indexed(service.get_skills("qa-engineer", industry, "mid"))
        assert control not in skills
        roadmap = service.get_roadmap("qa-engineer", industry, "mid")
        assert service.catalog.skills[control].name in {s.name for s in all_skills(roadmap)}


def test_native_component_capabilities_do_not_create_web_framework_categories(service):
    for role in ["android-developer", "ios-developer", "mobile-engineer"]:
        roadmap = service.get_roadmap(role, "saas", "staff")
        categories = {category.name for category in roadmap.hard_skills}
        assert "Frontend Frameworks & UI" not in categories
        assert "Accessible component libraries" in {skill.name for skill in all_skills(roadmap)}


def test_real_multi_ecosystem_tools_keep_all_associations(service):
    ai = indexed(service.get_skills("ai-engineer"))
    assert ai["langgraph"].technology_ecosystems == ["Python", "JavaScript / TypeScript"]
    assert {"langchain", "langgraph", "llama-index"} <= ai.keys()
    qa = indexed(service.get_skills("qa-engineer"))
    assert set(qa["playwright"].technology_ecosystems) == {
        "JavaScript / TypeScript",
        "Python",
        "Java / JVM",
        ".NET",
    }


def test_ambiguous_canonical_skill_names_are_rejected(editable_data):
    mutate(editable_data, "skills/technologies.json", lambda d: d["java"].update(name=" PYTHON "))
    with pytest.raises(CatalogError, match="Duplicate skill name"):
        Catalog(editable_data)
