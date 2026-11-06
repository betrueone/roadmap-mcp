import json
from itertools import product

import pytest

from roadmap_mcp.catalog import Catalog, LookupError
from roadmap_mcp.service import RoadmapService

from .conftest import all_categories, all_skills


def test_senior_backend_fintech(service):
    roadmap = service.get_roadmap("Backend Engineer", "Fintech", "Senior")
    skills = {skill.name for skill in all_skills(roadmap)}
    assert {
        "Unit testing",
        "Integration testing",
        "RESTful APIs",
        "Relational schema design",
        "Schema validation",
        "Deployment health checks and rollbacks",
        "Structured logging",
        "Application metrics instrumentation",
        "Distributed tracing",
        "Transaction isolation and locking",
        "Timeouts, retries, and circuit breakers",
        "Transactional outbox and sagas",
        "Technical leadership",
        "Financial data correctness",
        "PII redaction and data minimization",
        "Audit event logging",
        "Idempotent payment workflows",
        "Financial reconciliation",
        "Incident triage and recovery",
        "Git",
        "Session and token authentication",
        "Role-based and resource-level authorization",
        "Database indexing and query tuning",
        "Cache invalidation and expiration",
        "Message acknowledgments and dead-letter queues",
        "Docker",
        "Event schema versioning and replay",
        "Financial ledger modeling",
        "Payment event handling",
        "Settlement and payout processing",
    } <= skills
    assert {
        "Cross-team technical strategy",
        "API design",
        "System design",
        "HTTP and networking fundamentals",
        "Backend framework development",
        "React",
        "HL7 FHIR",
        "Commerce analytics models",
    }.isdisjoint(skills)


@pytest.mark.parametrize("include_descriptions", [True, False])
def test_specific_protocols_remain_useful_in_both_response_modes(service, include_descriptions):
    roadmap = service.get_roadmap(
        "Backend Engineer", "Fintech", "Mid-level", include_descriptions=include_descriptions
    )
    names = {skill.name for skill in all_skills(roadmap)}
    assert {"RESTful APIs", "OpenAPI specifications", "OAuth 2.0", "OpenID Connect"} <= names
    assert {"OAuth", "OpenID", "API design", "HTTP and networking fundamentals"}.isdisjoint(names)


@pytest.mark.parametrize(
    "role, included, excluded",
    [
        (
            "Frontend Engineer",
            {"Cross-browser compatibility testing", "Browser error and performance telemetry"},
            {"Web platform fundamentals", "Frontend build tooling", "Distributed tracing"},
        ),
        (
            "Data Engineer",
            {"Data quality assertions", "Event-time windows and late data handling"},
            {"Data pipelines and orchestration", "Python for data processing"},
        ),
        (
            "Android Developer",
            {"Process recreation and app lifecycle handling", "Mobile crash diagnostics"},
            {"Observability", "Distributed tracing"},
        ),
        (
            "AI Engineer",
            {"Structured outputs", "Agent workflows"},
            {"Large language model fundamentals", "Observability"},
        ),
        (
            "Machine Learning Engineer",
            {"Classification and regression pipelines", "Leakage-safe model validation"},
            {"Linear algebra", "Probability", "System design"},
        ),
        (
            "Cybersecurity Engineer",
            {"DNS and routing diagnostics", "Penetration testing"},
            {"Security fundamentals", "Debugging and troubleshooting"},
        ),
    ],
)
def test_curated_profiles_distinguish_implementation_from_broad_foundations(
    service, role, included, excluded
):
    names = {skill.name for skill in all_skills(service.get_roadmap(role, "SaaS", "Senior"))}
    assert included <= names
    assert excluded.isdisjoint(names)


def test_aliases_resolve_to_identical_roadmap(service):
    canonical = service.get_roadmap("backend-engineer", "fintech", "senior")
    alias = service.get_roadmap("  BACKEND   DEVELOPER ", "Financial Technology", "Sr.")
    assert canonical == alias


def test_all_supported_combinations_return_only_unique_skills_and_descriptions(service, catalog):
    combinations = 0
    for role, industry, level in product(catalog.roles, catalog.industries, catalog.levels):
        if role not in catalog.industries[industry].role_requirements:
            continue
        roadmap = service.get_roadmap(role, industry, level)
        combinations += 1
        assert all_skills(roadmap)
        assert len({skill.name for skill in all_skills(roadmap)}) == len(all_skills(roadmap))
        payload = roadmap.model_dump()
        assert set(payload) == {"hard_skills", "soft_skills", "industry_context"}
        names = [category.name for category in all_categories(roadmap)]
        assert len(names) == len(set(names))
        for kind in ("hard", "soft"):
            categories = payload[f"{kind}_skills"]
            assert [category["name"] for category in categories] == [
                category.name
                for category in catalog.categories.values()
                if category.type == kind and category.name in names
            ]
            for category in categories:
                assert set(category) == {"name", "skills"}
                assert category["name"] and category["skills"]
                for skill in category["skills"]:
                    assert set(skill) == {"name", "description"}
                    assert skill["name"] and skill["description"]
    assert combinations == len(catalog.roles) * len(catalog.industries) * len(catalog.levels)


def test_seniority_is_cumulative_and_staff_adds_strategy(service):
    previous = set()
    for level in ["junior", "mid", "senior", "staff"]:
        roadmap = service.get_roadmap("backend-engineer", "fintech", level)
        skills = {skill.name for skill in all_skills(roadmap)}
        assert previous <= skills
        if level == "junior":
            assert "Timeouts, retries, and circuit breakers" not in skills
            assert "Financial reconciliation" not in skills
        if level != "staff":
            assert "Cross-team technical strategy" not in skills
        previous = skills
    assert "Cross-team technical strategy" in skills


def test_industry_and_role_change_requirements(service):
    health = service.get_roadmap("backend-engineer", "healthcare", "senior")
    frontend = service.get_roadmap("frontend-engineer", "fintech", "senior")
    assert "HL7 FHIR" in {skill.name for skill in all_skills(health)}
    assert "Idempotent payment workflows" not in {skill.name for skill in all_skills(health)}
    assert "Reliable payment interfaces" in {skill.name for skill in all_skills(frontend)}
    assert "Transaction isolation and locking" not in {skill.name for skill in all_skills(frontend)}


def test_overlapping_role_and_industry_skills_appear_once(service):
    roadmap = service.get_roadmap("frontend-engineer", "ecommerce", "senior")
    assert [skill.name for skill in all_skills(roadmap)].count("Web performance") == 1


def test_backend_fintech_groups_skills_by_technical_area(service, catalog):
    roadmap = service.get_roadmap("backend-engineer", "fintech", "senior")
    category_ids = {
        category.name: identifier for identifier, category in catalog.categories.items()
    }
    categories = {
        category_ids[category.name]: {s.name for s in category.skills}
        for category in all_categories(roadmap)
    }
    assert {"Python", "Java", "Go"} <= categories["programming-languages"]
    assert {"PostgreSQL", "Redis", "SQL"} <= categories["databases-caching"]
    assert {"Apache Kafka", "RabbitMQ"} <= categories["messaging-streaming"]
    assert {"Docker", "Kubernetes"} <= categories["containers-deployment"]
    assert "Stripe API" in categories["payments-finance"]
    assert "Financial reconciliation" not in categories["payments-finance"]
    assert "Financial reconciliation" in {concept.name for concept in roadmap.industry_context}
    assert {"healthcare", "e-commerce", "frontend-frameworks"}.isdisjoint(categories)


def test_backend_fintech_separates_technical_skills_domain_context_and_leadership(service):
    roadmap = service.get_roadmap("backend-engineer", "fintech", "staff")
    hard = {s.name for category in roadmap.hard_skills for s in category.skills}
    soft = {s.name for category in roadmap.soft_skills for s in category.skills}
    assert {
        "Python",
        "PostgreSQL",
        "Docker",
        "RESTful APIs",
        "Transactional outbox and sagas",
        "Architecture decision records (ADRs)",
        "Incident triage and recovery",
    } <= hard
    context = {concept.name for concept in roadmap.industry_context}
    assert "Financial reconciliation" in context
    assert context.isdisjoint(hard | soft)
    assert soft == {
        "Technical leadership",
        "Cross-team technical strategy",
        "Engineering standards and governance",
    }
    assert hard.isdisjoint(soft)
    assert [category.name for category in roadmap.soft_skills] == ["Technical Leadership"]


@pytest.mark.parametrize("level", ["junior", "mid"])
def test_profiles_without_matching_soft_skills_return_an_empty_section(service, level):
    roadmap = service.get_roadmap("backend-engineer", "fintech", level)
    assert roadmap.hard_skills
    assert roadmap.soft_skills == []
    assert roadmap.model_dump()["soft_skills"] == []


def test_category_type_is_read_from_source_data(editable_data):
    path = editable_data / "categories.json"
    categories = json.loads(path.read_text())
    categories["technical-leadership"]["type"] = "hard"
    path.write_text(json.dumps(categories))
    for skill_path in (editable_data / "skills").glob("*.json"):
        skills = json.loads(skill_path.read_text())
        for skill_id in categories["technical-leadership"]["skill_ids"]:
            if skill_id in skills:
                skills[skill_id]["type"] = "professional_method"
        skill_path.write_text(json.dumps(skills))
    roadmap = RoadmapService(Catalog(editable_data)).get_roadmap(
        "backend-engineer", "fintech", "senior"
    )
    assert roadmap.soft_skills == []
    assert "Technical leadership" in {
        skill.name for category in roadmap.hard_skills for skill in category.skills
    }


def test_category_assignments_and_order_come_from_source_files(editable_data):
    path = editable_data / "categories.json"
    categories = json.loads(path.read_text())
    categories["programming-languages"]["skill_ids"].remove("python")
    categories = {
        "custom-python": {"name": "Python Stack", "type": "hard", "skill_ids": ["python"]},
        **categories,
    }
    path.write_text(json.dumps(categories))
    roadmap = RoadmapService(Catalog(editable_data)).get_roadmap(
        "backend-engineer", "fintech", "senior"
    )
    assert all_categories(roadmap)[0].name == "Python Stack"
    assert [s.name for s in all_categories(roadmap)[0].skills] == ["Python"]
    programming = next(c for c in all_categories(roadmap) if c.name == "Programming Languages")
    assert "Python" not in {s.name for s in programming.skills}
    assert [s.name for s in all_skills(roadmap)].count("Python") == 1


@pytest.mark.parametrize(
    "role, included, excluded",
    [
        (
            "backend-engineer",
            {"RESTful APIs", "Payment lifecycle modeling"},
            {
                "Financial ledger modeling",
                "Settlement and payout processing",
                "Data partitioning and sharding",
            },
        ),
        (
            "frontend-engineer",
            {"JavaScript", "TypeScript", "HTML", "Financial interface formatting"},
            {
                "Server rendering and hydration",
                "Payment authentication interfaces",
                "Frontend module and dependency boundaries",
            },
        ),
        (
            "data-engineer",
            {"Columnar file schemas and partitioning", "Batch data ingestion"},
            {"Change data capture", "Financial reporting datasets", "Data platform architecture"},
        ),
    ],
)
def test_junior_profiles_filter_advanced_role_and_industry_skills(
    service, role, included, excluded
):
    skills = {skill.name for skill in all_skills(service.get_roadmap(role, "fintech", "junior"))}
    assert included <= skills
    assert excluded.isdisjoint(skills)


@pytest.mark.parametrize(
    "role, industry, included, excluded",
    [
        (
            "frontend-engineer",
            "e-commerce",
            {
                "TypeScript",
                "Client-side routing",
                "Shopping cart state management",
                "Technical SEO for commerce",
            },
            {
                "Financial ledger modeling",
                "Clinical terminology mapping",
                "Data pipeline observability",
            },
        ),
        (
            "data-engineer",
            "healthcare",
            {
                "SQL window functions and CTEs",
                "Change data capture",
                "Clinical data validation",
                "Healthcare data de-identification",
            },
            {
                "Financial reporting datasets",
                "Frontend module and dependency boundaries",
                "Order processing workflows",
            },
        ),
    ],
)
def test_enriched_profiles_keep_role_and_industry_specific_skills(
    service, role, industry, included, excluded
):
    skills = {skill.name for skill in all_skills(service.get_roadmap(role, industry, "mid"))}
    assert included <= skills
    assert excluded.isdisjoint(skills)


@pytest.mark.parametrize(
    "role, industry, category_name, first_skill, included, excluded",
    [
        (
            "backend-engineer",
            "fintech",
            "Programming Languages",
            "Python",
            {
                "Java",
                "Go",
                "C#",
                "Node.js",
                "Spring Boot",
                "FastAPI",
                "PostgreSQL",
                "Redis",
                "Apache Kafka",
                "RabbitMQ",
                "Docker",
                "Kubernetes",
                "Stripe API",
            },
            {"React", "Apache Airflow", "Shopify Storefront API", "SMART on FHIR"},
        ),
        (
            "frontend-engineer",
            "e-commerce",
            "Web Platform",
            "HTML",
            {
                "CSS",
                "JavaScript",
                "TypeScript",
                "React",
                "Vue.js",
                "Angular",
                "Next.js",
                "Vite",
                "Tailwind CSS",
                "Playwright",
                "Shopify Storefront API",
            },
            {"PostgreSQL", "Spring Boot", "Apache Spark", "Stripe API"},
        ),
        (
            "data-engineer",
            "healthcare",
            "Programming Languages",
            "Python",
            {
                "SQL",
                "pandas",
                "NumPy",
                "Apache Airflow",
                "dbt",
                "Apache Spark",
                "Snowflake",
                "Google BigQuery",
                "Delta Lake",
                "HL7 FHIR",
            },
            {"React", "Spring Boot", "Stripe API", "Shopify GraphQL Admin API"},
        ),
    ],
)
def test_exact_technology_names_are_returned_for_relevant_profiles(
    service, role, industry, category_name, first_skill, included, excluded
):
    roadmap = service.get_roadmap(role, industry, "senior")
    names = {skill.name for skill in all_skills(roadmap)}
    category = next(c for c in all_categories(roadmap) if c.name == category_name)
    assert category.skills[0].name == first_skill
    assert included <= names
    assert excluded.isdisjoint(names)


@pytest.mark.parametrize(
    "args, dimension",
    [
        (("unlisted role", "fintech", "senior"), "role"),
        (("backend-engineer", "unknown", "senior"), "industry"),
        (("backend-engineer", "fintech", "principal"), "seniority"),
        (("../../catalog.json", "fintech", "senior"), "role"),
    ],
)
def test_unknown_inputs_never_fall_back(service, args, dimension):
    with pytest.raises(LookupError, match=f"Unknown {dimension}"):
        service.get_roadmap(*args)


def test_unsupported_combination_never_falls_back(editable_data):
    path = editable_data / "industries/fintech.json"
    data = json.loads(path.read_text())
    del data["role_requirements"]["backend-engineer"]
    path.write_text(json.dumps(data))
    service = RoadmapService(Catalog(editable_data))
    with pytest.raises(LookupError, match="No roadmap"):
        service.get_roadmap("backend-engineer", "fintech", "senior")
    coverage = next(
        item for item in service.list_catalog().coverage if item.role_id == "backend-engineer"
    )
    assert "fintech" not in coverage.industry_ids


@pytest.mark.parametrize(
    "role, industry, level",
    [
        ("Backend Engineer", "Fintech", "Senior"),
        ("Backend Engineer", "Fintech", "Junior"),
        ("UX Designer", "Healthcare", "Senior"),
    ],
)
def test_description_option_preserves_skills_categories_and_catalog(service, role, industry, level):
    full = service.get_roadmap(role, industry, level)
    assert full == service.get_roadmap(role, industry, level, include_descriptions=True)

    compact = service.get_roadmap(role, industry, level, include_descriptions=False)
    expected = {
        section: [
            {
                "name": category["name"],
                "skills": [{"name": skill["name"]} for skill in category["skills"]],
            }
            for category in categories
        ]
        for section, categories in full.model_dump().items()
        if section != "industry_context"
    }
    expected["industry_context"] = [{"name": concept.name} for concept in full.industry_context]
    assert compact.model_dump() == expected
    assert service.get_roadmap(role, industry, level) == full
