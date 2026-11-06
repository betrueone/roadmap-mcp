import pytest
from mcp import Client

from roadmap_mcp.models import Roadmap
from roadmap_mcp.server import create_server

from .conftest import all_skills


def technical_and_context_names(roadmap):
    return {
        *[skill.name for category in roadmap.hard_skills for skill in category.skills],
        *[concept.name for concept in roadmap.industry_context],
    }


def test_broad_catalog_has_explicit_complete_industry_coverage(catalog, service):
    assert len(catalog.roles) >= 20
    assert len(catalog.industries) >= 15
    for industry in catalog.industries.values():
        assert set(industry.role_requirements) == set(catalog.roles)
        assert all(industry.role_requirements.values())
    for coverage in service.list_catalog().coverage:
        assert set(coverage.industry_ids) == set(catalog.industries)
    for dimension, entities in [("role", catalog.roles), ("industry", catalog.industries)]:
        for entity in entities.values():
            for alias in entity.aliases:
                assert catalog.resolve(dimension, alias.upper()) == entity.id


@pytest.mark.parametrize(
    "role, industry, included, excluded",
    [
        (
            "Full Stack Engineer",
            "SaaS",
            {"React", "PostgreSQL", "Subscription lifecycle management"},
            {"Swift", "Clinical terminology mapping"},
        ),
        (
            "DevOps Engineer",
            "Manufacturing",
            {"Terraform", "Ansible", "GitHub Actions", "Industrial edge reliability"},
            {"Figma", "Power BI"},
        ),
        (
            "Site Reliability Engineer",
            "Gaming",
            {
                "Prometheus",
                "Grafana",
                "Service level indicators and error budgets",
                "Game session reliability",
            },
            {"Power BI", "SwiftUI"},
        ),
        (
            "Cloud Engineer",
            "Energy",
            {"AWS", "Azure", "Google Cloud", "Terraform", "Energy data service reliability"},
            {"Jetpack Compose", "PyTorch"},
        ),
        (
            "Platform Engineer",
            "SaaS",
            {"Kubernetes", "Helm", "Argo CD", "SaaS workload isolation"},
            {"PyTorch", "Figma"},
        ),
        (
            "QA Engineer",
            "Banking",
            {"Playwright", "Selenium", "Postman", "Banking balance invariant testing"},
            {"PyTorch", "SwiftUI"},
        ),
        (
            "Android Developer",
            "Education",
            {"Kotlin", "Jetpack Compose", "Room", "Learner and educator interfaces"},
            {"SwiftUI", "React"},
        ),
        (
            "iOS Developer",
            "Media",
            {"Swift", "SwiftUI", "Xcode", "HTTP Live Streaming (HLS)"},
            {"Kotlin", "Jetpack Compose"},
        ),
        (
            "Mobile Engineer",
            "E-commerce",
            {"React Native", "Flutter", "Dart", "Shopping cart state management"},
            {"Web performance", "Technical SEO for commerce"},
        ),
        (
            "Data Analyst",
            "Insurance",
            {"SQL", "Excel", "Power BI", "Insurance loss analytics"},
            {"Kubernetes", "PyTorch"},
        ),
        (
            "Data Scientist",
            "Fintech",
            {"PyTorch", "scikit-learn", "Financial fraud modeling"},
            {"React", "PostgreSQL"},
        ),
        (
            "Machine Learning Engineer",
            "Manufacturing",
            {"TensorFlow", "Model serving", "Predictive maintenance modeling"},
            {"Figma", "Learning Tools Interoperability (LTI)"},
        ),
        (
            "AI Engineer",
            "Government",
            {
                "LangChain",
                "Qdrant",
                "Retrieval-Augmented Generation (RAG)",
                "Public guidance retrieval",
            },
            {"PyTorch", "Shopify Storefront API"},
        ),
        (
            "Cybersecurity Engineer",
            "Banking",
            {"Nmap", "Wireshark", "Banking transaction authorization"},
            {"Figma", "React"},
        ),
        (
            "UX Designer",
            "Healthcare",
            {"Figma", "Prototyping", "Accessible healthcare workflows"},
            {"Python", "SQL", "Kubernetes"},
        ),
        (
            "Product Manager",
            "Logistics",
            {"Jira", "Linear", "Logistics performance analytics"},
            {"Terraform", "Shipment tracking integration"},
        ),
        (
            "Engineering Manager",
            "Telecom",
            {
                "Engineering budget planning",
                "Engineering organization design",
                "Telecom service observability",
            },
            {"PyTorch", "Figma"},
        ),
    ],
)
def test_new_roles_return_concrete_relevant_hard_skills(
    service, role, industry, included, excluded
):
    roadmap = service.get_roadmap(role, industry, "senior")
    names = technical_and_context_names(roadmap)
    assert included <= names
    assert excluded.isdisjoint(names)
    assert names.isdisjoint(s.name for c in roadmap.soft_skills for s in c.skills)


@pytest.mark.parametrize(
    "industry, app_skill, analytical_skill",
    [
        ("SaaS", "Subscription lifecycle management", "Subscription revenue analytics"),
        ("Education", "Learning platform integration", "Learning analytics"),
        ("Banking", "Banking transaction posting", "Credit portfolio analytics"),
        ("Insurance", "Claims processing workflows", "Insurance loss analytics"),
        ("Telecom", "Telecom service provisioning", "Telecom service analytics"),
        ("Media", "Media transcoding workflows", "Audience engagement analytics"),
        ("Gaming", "Matchmaking services", "Game engagement analytics"),
        ("Logistics", "Shipment tracking integration", "Logistics performance analytics"),
        ("Manufacturing", "Production system integration", "Production performance analytics"),
        ("Energy", "Meter data workflows", "Energy consumption analytics"),
        ("Real Estate", "Geospatial property search", "Property market analytics"),
        ("Government", "Public service case management", "Public service performance analytics"),
    ],
)
def test_new_industries_distinguish_implementation_and_analytics(
    service, industry, app_skill, analytical_skill
):
    backend = technical_and_context_names(
        service.get_roadmap("Backend Engineer", industry, "senior")
    )
    analyst = technical_and_context_names(service.get_roadmap("Data Analyst", industry, "senior"))
    assert app_skill in backend and app_skill not in analyst
    assert analytical_skill in analyst and analytical_skill not in backend


@pytest.mark.parametrize(
    "role, industry, advanced_skill, first_level",
    [
        ("Android Developer", "Education", "Offline synchronization", "mid"),
        ("AI Engineer", "Government", "Retrieval-Augmented Generation (RAG)", "mid"),
        ("Machine Learning Engineer", "Banking", "Credit risk modeling", "senior"),
        ("Data Scientist", "Energy", "Energy demand forecasting", "senior"),
        ("Product Manager", "SaaS", "Product portfolio management", "staff"),
        ("UX Designer", "Healthcare", "Mentoring and coaching", "senior"),
        ("Engineering Manager", "Telecom", "Engineering organization design", "senior"),
    ],
)
def test_new_profiles_gate_advanced_skills_and_remain_cumulative(
    service, role, industry, advanced_skill, first_level
):
    previous = set()
    eligible = False
    for level in ["junior", "mid", "senior", "staff"]:
        eligible = eligible or level == first_level
        roadmap = service.get_roadmap(role, industry, level)
        names = {s.name for s in all_skills(roadmap)}
        assert previous < names
        assert (advanced_skill in names) == eligible
        previous = names


def test_design_and_management_keep_methods_hard_and_interpersonal_skills_soft(service):
    roadmap = service.get_roadmap("Engineering Manager", "SaaS", "senior")
    assert {"Engineering budget planning", "Hiring process design"} <= technical_and_context_names(
        roadmap
    )
    soft = {skill.name for category in roadmap.soft_skills for skill in category.skills}
    assert {"Mentoring and coaching", "Delegation", "Conflict resolution"} <= soft
    assert {"Engineering budget planning", "Hiring process design"}.isdisjoint(soft)


@pytest.mark.parametrize(
    "role, industry, expected",
    [
        ("ml engineer", "insurtech", "Insurance risk modeling"),
        ("sre", "utilities", "Energy data service reliability"),
        ("product designer", "edtech", "Learner and educator interfaces"),
    ],
)
async def test_mcp_serves_new_roles_and_industries_with_aliases(catalog, role, industry, expected):
    async with Client(create_server(catalog)) as client:
        result = await client.call_tool(
            "get_roadmap",
            {"role_name": role, "industry": industry, "seniority_level": "Senior"},
        )
        assert not result.is_error
        roadmap = Roadmap.model_validate(result.structured_content)
        assert expected in technical_and_context_names(roadmap)
