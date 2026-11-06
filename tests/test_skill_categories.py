import pytest

from roadmap_mcp.catalog import Catalog, CatalogError
from roadmap_mcp.models import SkillsResponse
from roadmap_mcp.service import RoadmapService
from roadmap_mcp.skill_categories import (
    _SKILL_GROUPS,
    NONTECHNICAL_ROLE_CATEGORIES,
    TECHNICAL_CATEGORIES,
    response_category,
)
from roadmap_mcp.skills_text import format_skills

from .test_catalog import mutate


def test_category_assignments_reference_real_skills_once(catalog):
    assignments = [skill_id for ids in _SKILL_GROUPS.values() for skill_id in ids.split()]
    assert len(assignments) == len(set(assignments))
    assert set(assignments) <= catalog.skills.keys()
    permitted = set(TECHNICAL_CATEGORIES) | {
        name for names in NONTECHNICAL_ROLE_CATEGORIES.values() for name in names
    }
    assert _SKILL_GROUPS.keys() <= permitted


def test_data_engineer_uses_split_technical_categories(service):
    result = service.get_skills("Data Engineer", seniority_level="Senior")
    by_id = {skill.id: response_category(skill.id, skill.category) for skill in result.skills}
    assert by_id["python"] == by_id["sql"] == "Programming Languages"
    assert by_id["apache-airflow"] == "Workflow Orchestration"
    assert by_id["dbt"] == "Data Modeling & Transformation"
    assert by_id["apache-spark"] == "Data Processing & ETL/ELT"
    assert by_id["snowflake"] == "Data Warehouses & Lakehouses"
    assert by_id["apache-kafka"] == "Streaming & Change Data Capture"
    assert by_id["data-quality"] == "Data Quality & Governance"
    response = SkillsResponse.from_result(result)
    assert set(response.categories) <= set(TECHNICAL_CATEGORIES)


def test_industry_options_and_nontechnical_categories(service):
    result = service.get_skills("Backend Engineer", "Fintech", "Senior")
    by_id = {skill.id: response_category(skill.id, skill.category) for skill in result.skills}
    assert by_id["stripe-api"] == "Third-Party Integrations"
    assert by_id["payment-idempotency"] == "APIs & Service Integration"
    for role, category in [
        ("UX Designer", "User Experience & Design"),
        ("Product Manager", "Product Management"),
        ("Engineering Manager", "Engineering Management"),
    ]:
        summary = SkillsResponse.from_result(service.get_skills(role))
        assert category in set(summary.categories)


def test_every_role_has_an_explicit_map(catalog):
    for role in catalog.roles.values():
        assert role.response_categories
        assert len(role.response_categories) == len(set(role.response_categories))
        allowed = set(TECHNICAL_CATEGORIES) | set(NONTECHNICAL_ROLE_CATEGORIES.get(role.id, ()))
        assert set(role.response_categories) <= allowed
    assert catalog.roles["data-engineer"].response_categories[:5] == [
        "Programming Languages",
        "Data Processing & ETL/ELT",
        "Data Warehouses & Lakehouses",
        "Data Modeling & Transformation",
        "Workflow Orchestration",
    ]
    assert catalog.roles["qa-engineer"].response_categories[0] == "Testing & Quality Engineering"
    assert catalog.roles["ux-designer"].response_categories[0] == "User Experience & Design"


def test_legacy_categories_cannot_return_through_role_or_industry_skills(service):
    for role in service.catalog.roles.values():
        for industry in service.catalog.industries.values():
            result = service.get_skills(role.id, industry.id)
            summary = SkillsResponse.from_result(result)
            assert set(summary.categories) <= set(role.response_categories)
            assert set(summary.categories) == {
                response_category(skill.id, skill.category) for skill in result.skills
            }
    data = SkillsResponse.from_result(service.get_skills("Data Engineer", "Banking"))
    assert "Banking" not in set(data.categories)
    assert "design-systems" in {s.id for s in service.get_skills("Frontend Engineer").skills}


def test_direct_industry_additions_require_role_category_coverage(editable_data):
    mutate(
        editable_data,
        "roles/backend-engineer.json",
        lambda role: role["response_categories"].remove("Third-Party Integrations"),
    )
    with pytest.raises(CatalogError, match="industry:banking/role:backend-engineer: missing"):
        Catalog(editable_data)


@pytest.mark.parametrize("industry", [None, "Fintech", "Healthcare"])
@pytest.mark.parametrize("seniority", ["Junior", "Senior"])
def test_role_order_survives_industry_seniority_and_limit(service, industry, seniority):
    result = service.get_skills("etl developer", industry, seniority, limit=4)
    summary = SkillsResponse.from_result(result)
    assert summary.categories == [
        "Programming Languages",
        "Data Processing & ETL/ELT",
        "CI/CD & DevOps",
    ]
    assert "Data Warehouses & Lakehouses" not in set(summary.categories)
    assert format_skills(result).splitlines()[0] == (
        "categories: Programming Languages, Data Processing & ETL/ELT, CI/CD & DevOps"
    )


def test_role_file_controls_order_without_changing_skills(editable_data, service):
    mutate(
        editable_data,
        "roles/data-engineer.json",
        lambda role: role["response_categories"].reverse(),
    )
    original = service.get_skills("Data Engineer")
    updated = RoadmapService(Catalog(editable_data)).get_skills("Data Engineer")
    assert original.skills == updated.skills
    original_names = SkillsResponse.from_result(original).categories
    updated_names = SkillsResponse.from_result(updated).categories
    assert updated_names == list(reversed(original_names))


def test_shared_industry_additions_respect_role_categories(editable_data):
    mutate(
        editable_data,
        "industries/saas.json",
        lambda industry: industry["requirements"].append({"skill_id": "rag"}),
    )
    service = RoadmapService(Catalog(editable_data))
    assert "rag" in {skill.id for skill in service.get_skills("AI Engineer", "SaaS").skills}
    assert "rag" not in {
        skill.id for skill in service.get_skills("Frontend Engineer", "SaaS").skills
    }


@pytest.mark.parametrize(
    ("edit", "expected"),
    [
        (lambda role: role.pop("response_categories"), "response_categories"),
        (lambda role: role.update(response_categories=[]), "response_categories"),
        (
            lambda role: role["response_categories"].append("Programming Languages"),
            "duplicate response category",
        ),
        (
            lambda role: role["response_categories"].append("Unknown Category"),
            "unknown response categories",
        ),
        *[
            (
                lambda role, name=name: role["response_categories"].append(name),
                f"unknown response categories: {name}",
            )
            for name in ["Banking", "Data Engineering & Analytics", "Product Management"]
        ],
        (
            lambda role: role["response_categories"].remove("Workflow Orchestration"),
            "missing response categories: Workflow Orchestration",
        ),
    ],
)
def test_invalid_role_category_maps_rejected(editable_data, edit, expected):
    mutate(editable_data, "roles/data-engineer.json", edit)
    with pytest.raises(CatalogError, match=expected):
        Catalog(editable_data)


def test_all_curated_options_and_required_categories_survive_role_only_discovery(service):
    for role in service.catalog.roles.values():
        result = service.get_skills(role.id)
        assert {skill.id for skill in result.skills} == {
            option.skill_id for option in role.skill_options
        }, role.id
        assert result.available_count == result.returned_count == len(role.skill_options)
        assert set(role.required_categories) <= set(SkillsResponse.from_result(result).categories)


@pytest.mark.parametrize(
    "role, industry, seniority, restored",
    [
        ("machine-learning-engineer", "banking", "mid", {"credit-portfolio-analytics"}),
        ("qa-engineer", "fintech", "senior", {"financial-reconciliation"}),
        ("data-analyst", "fintech", "mid", {"financial-reconciliation"}),
        ("qa-engineer", "e-commerce", "mid", {"inventory-consistency"}),
        ("frontend-engineer", "e-commerce", "mid", {"commerce-event-tracking"}),
        ("ux-designer", "fintech", "mid", {"financial-disclosure-design"}),
    ],
)
def test_authored_industry_skills_survive_category_selection(
    service, role, industry, seniority, restored
):
    result = service.get_skills(role, industry, seniority)
    assert result.available_count <= 50
    assert restored <= {skill.id for skill in result.skills}


@pytest.mark.parametrize(
    "industry, skill_id",
    [
        ("e-commerce", "commerce-domain"),
        ("saas", "saas-domain"),
        ("education", "education-domain"),
        ("banking", "banking-domain"),
        ("insurance", "insurance-domain"),
        ("telecommunications", "telecom-domain"),
        ("media-entertainment", "media-domain"),
        ("gaming", "gaming-domain"),
        ("logistics", "logistics-domain"),
        ("manufacturing", "manufacturing-domain"),
        ("energy", "energy-domain"),
        ("real-estate", "real-estate-domain"),
        ("government", "government-domain"),
    ],
)
def test_applied_domain_modeling_is_discoverable(service, industry, skill_id):
    result = service.get_skills("backend-engineer", industry, "junior")
    assert skill_id in {skill.id for skill in result.skills}
    assert "Data Modeling & Transformation" in SkillsResponse.from_result(result).categories


@pytest.mark.parametrize(
    "skill_id, expected",
    [
        ("financial-data", "Data Modeling & Transformation"),
        ("healthcare-data", "Data Modeling & Transformation"),
        ("commerce-event-tracking", "BI & Analytics"),
        ("financial-reconciliation", "Data Quality & Governance"),
        ("fraud-signals", "Security & Authentication"),
        ("financial-disclosure-design", "User Experience & Design"),
        ("hilt", "Architecture & System Design"),
        ("kotlin-coroutines", "Mobile Development"),
        ("combine", "Mobile Development"),
        ("html-semantics", "Web Platform"),
        ("css-layout", "Web Platform"),
        ("nodejs", "Backend Frameworks & Runtimes"),
        ("design-systems", "Frontend & UI Engineering"),
        ("design-tokens", "Frontend & UI Engineering"),
    ],
)
def test_response_categories_describe_the_authored_work(catalog, skill_id, expected):
    source = catalog.categories[catalog.skill_categories[skill_id]].name
    assert response_category(skill_id, source) == expected


@pytest.mark.parametrize(
    "role, removed, expected",
    [
        ("data-analyst", "Product Management", "Product Management"),
        ("qa-engineer", "Engineering Management", "Engineering Management"),
    ],
)
def test_curated_professional_methods_cannot_be_silently_filtered(
    editable_data, role, removed, expected
):
    mutate(
        editable_data,
        f"roles/{role}.json",
        lambda data: data["response_categories"].remove(removed),
    )
    with pytest.raises(CatalogError, match=f"missing response categories: {expected}"):
        Catalog(editable_data)


@pytest.mark.parametrize(
    "edit, expected",
    [
        (lambda role: role.pop("required_categories"), "required_categories"),
        (lambda role: role.update(required_categories=[]), "required_categories"),
        (
            lambda role: role["required_categories"].append(" Programming Languages "),
            "duplicate required category",
        ),
        (
            lambda role: role["required_categories"].append("Third-Party Integrations"),
            "required categories without curated skills: Third-Party Integrations",
        ),
        (
            lambda role: role["required_categories"].append("Unknown Category"),
            "required categories outside response map: Unknown Category",
        ),
        (
            lambda role: role.update(
                skill_options=[
                    option
                    for option in role["skill_options"]
                    if option["skill_id"] != "structured-logging"
                ]
            ),
            "required categories without curated skills: Observability & Reliability",
        ),
    ],
)
def test_required_category_definitions_are_validated(editable_data, edit, expected):
    mutate(editable_data, "roles/backend-engineer.json", edit)
    with pytest.raises(CatalogError, match=expected):
        Catalog(editable_data)


def test_required_categories_do_not_override_seniority_or_result_limits(service):
    result = service.get_skills("data-engineer", seniority_level="junior", limit=1)
    assert [skill.id for skill in result.skills] == ["python"]
    assert SkillsResponse.from_result(result).categories == ["Programming Languages"]


def test_new_applied_skills_require_a_permitted_category_projection(editable_data):
    mutate(
        editable_data,
        "skills/industries.json",
        lambda skills: skills.update(
            unmapped={
                "name": "Unmapped industry workflow",
                "description": "Implement a domain workflow.",
                "type": "implementation_capability",
            }
        ),
    )
    mutate(
        editable_data,
        "categories.json",
        lambda categories: categories["payments-finance"]["skill_ids"].append("unmapped"),
    )
    with pytest.raises(CatalogError, match="skill:unmapped: unknown response category"):
        Catalog(editable_data)
