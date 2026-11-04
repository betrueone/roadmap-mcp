import json

import pytest

from roadmap_mcp.catalog import Catalog, CatalogError


def mutate(directory, filename, edit):
    path = directory / filename
    data = json.loads(path.read_text())
    edit(data)
    path.write_text(json.dumps(data))


@pytest.mark.parametrize(
    "filename, edit, expected",
    [
        (
            "skills/backend.json",
            lambda d: d.update(
                python={"name": "Python", "description": "Write code.", "type": "language"}
            ),
            "Duplicate skill ID",
        ),
        (
            "skills/technologies.json",
            lambda d: d["python"].update(description=" "),
            "description",
        ),
        (
            "skills/technologies.json",
            lambda d: d["python"].pop("description"),
            "description",
        ),
        (
            "skills/technologies.json",
            lambda d: d["python"].update(resume_keywords=["Python"]),
            "Extra inputs",
        ),
        (
            "categories.json",
            lambda d: d["programming-languages"]["skill_ids"].append("missing"),
            "unknown skill missing",
        ),
        (
            "categories.json",
            lambda d: d["programming-languages"]["skill_ids"].append("python"),
            "exactly one category",
        ),
        (
            "categories.json",
            lambda d: d["testing"]["skill_ids"].append("python"),
            "exactly one category",
        ),
        (
            "categories.json",
            lambda d: d["programming-languages"]["skill_ids"].remove("python"),
            "Skills without a category: python",
        ),
        (
            "categories.json",
            lambda d: d["testing"].update(name=" PROGRAMMING LANGUAGES "),
            "Duplicate category name",
        ),
        (
            "categories.json",
            lambda d: d["testing"].update(skill_ids=[]),
            "skill_ids",
        ),
        (
            "categories.json",
            lambda d: d["testing"].pop("type"),
            "type",
        ),
        (
            "categories.json",
            lambda d: d["testing"].update(type="mixed"),
            "type",
        ),
        (
            "categories.json",
            lambda d: d["testing"].update(type=None),
            "type",
        ),
        (
            "roles/backend-engineer.json",
            lambda d: d.update(aliases=["Frontend Engineer"]),
            "Ambiguous role alias",
        ),
        (
            "roles/backend-engineer.json",
            lambda d: d["requirements"][0].update(skill_id="missing"),
            "unknown skill",
        ),
        (
            "roles/backend-engineer.json",
            lambda d: d["requirements"][0].update(minimum_seniority="unknown"),
            "unknown seniority",
        ),
        (
            "roles/backend-engineer.json",
            lambda d: d["requirements"].append(d["requirements"][0]),
            "duplicate requirement",
        ),
        (
            "industries/fintech.json",
            lambda d: d["role_requirements"].update(unknown=[]),
            "unknown role",
        ),
        ("seniority.json", lambda d: d["levels"][1].update(rank=0), "ranks must be unique"),
        (
            "roles/backend-engineer.json",
            lambda d: d["requirements"][0].update(target_proficiency="advanced"),
            "Extra inputs",
        ),
        (
            "seniority.json",
            lambda d: d["levels"][0].update(expectations=["Deliver features."]),
            "Extra inputs",
        ),
    ],
)
def test_invalid_catalog_fails_before_serving(editable_data, filename, edit, expected):
    mutate(editable_data, filename, edit)
    with pytest.raises(CatalogError, match=expected):
        Catalog(editable_data)


def test_duplicate_json_keys_rejected(editable_data):
    (editable_data / "skills/shared.json").write_text('{"programming":{}, "programming":{}}')
    with pytest.raises(CatalogError, match="Duplicate JSON key"):
        Catalog(editable_data)


def test_missing_categories_file_rejected(editable_data):
    (editable_data / "categories.json").unlink()
    with pytest.raises(CatalogError, match="categories.json"):
        Catalog(editable_data)


def test_empty_and_malformed_catalogs_rejected(tmp_path, editable_data):
    with pytest.raises(CatalogError, match="seniority.json"):
        Catalog(tmp_path)
    (editable_data / "roles/backend-engineer.json").write_text("{broken")
    with pytest.raises(CatalogError, match="backend-engineer.json"):
        Catalog(editable_data)


def test_stored_skills_have_explicit_classification(editable_data):
    for path in (editable_data / "skills").glob("*.json"):
        skills = json.loads(path.read_text())
        assert skills
        for skill in skills.values():
            expected = {"name", "description", "type"}
            if skill["type"] not in {
                "implementation_capability",
                "professional_method",
                "soft_skill",
            }:
                expected |= {"technology_family", "related_capabilities"}
            assert expected <= set(skill) <= expected | {"selection_group", "technology_ecosystems"}


def test_all_catalog_skills_are_used_by_selection_rules(catalog):
    referenced = {
        requirement.skill_id for role in catalog.roles.values() for requirement in role.requirements
    }
    for industry in catalog.industries.values():
        referenced.update(requirement.skill_id for requirement in industry.requirements)
        for requirements in industry.role_requirements.values():
            referenced.update(requirement.skill_id for requirement in requirements)
    assert referenced == catalog.skills.keys()


def test_source_data_stores_literal_technology_names(editable_data):
    skills = json.loads((editable_data / "skills/technologies.json").read_text())
    for skill_id, name in {
        "python": "Python",
        "java": "Java",
        "spring-boot": "Spring Boot",
        "postgresql": "PostgreSQL",
        "redis": "Redis",
        "apache-kafka": "Apache Kafka",
        "react": "React",
        "apache-airflow": "Apache Airflow",
    }.items():
        assert skills[skill_id]["name"] == name
        expected = {
            "name",
            "description",
            "type",
            "technology_family",
            "related_capabilities",
        }
        assert (
            expected
            <= set(skills[skill_id])
            <= expected | {"selection_group", "technology_ecosystems"}
        )


@pytest.mark.parametrize(
    "filename, edit, expected",
    [
        ("skills/technologies.json", lambda d: d["python"].pop("type"), "type"),
        ("skills/technologies.json", lambda d: d["python"].update(type="concept"), "type"),
        *[
            (
                "skills/technologies.json",
                lambda d, value=value: d["python"].update(technology_ecosystems=value),
                "technology_ecosystems",
            )
            for value in [None, "Python", [""], ["   "], [42]]
        ],
        (
            "skills/technologies.json",
            lambda d: d["python"].update(technology_ecosystems=["Python", " python "]),
            "duplicate technology ecosystem",
        ),
        *[
            (
                filename,
                lambda d, key=key: d[key].update(technology_ecosystems=["Python"]),
                "technology_ecosystems requires a technology",
            )
            for filename, key in [
                ("skills/ai.json", "rag"),
                ("skills/shared.json", "technical-leadership"),
                ("skills/analytics.json", "data-visualization"),
            ]
        ],
        *[
            (
                "skills/technologies.json",
                lambda d, value=value: d["pgvector"].update(selection_group=value),
                "selection_group",
            )
            for value in ["", "   ", 42, ["Vector Storage"]]
        ],
        (
            "skills/ai.json",
            lambda d: d["rag"].update(selection_group="Vector Storage"),
            "selection_group requires a technology",
        ),
        (
            "skills/technologies.json",
            lambda d: d["pgvector"].pop("technology_family"),
            "technology requires technology_family",
        ),
        *[
            (
                "skills/technologies.json",
                lambda d, value=value: d["pgvector"].update(technology_family=value),
                "technology_family",
            )
            for value in [None, "", "   ", 42]
        ],
        (
            "skills/ai.json",
            lambda d: d["rag"].update(technology_family="Vector Retrieval"),
            "technology_family requires a technology",
        ),
        (
            "skills/technologies.json",
            lambda d: d["pgvector"].update(related_capabilities=["nonexistent-capability"]),
            "unknown related capability",
        ),
        *[
            (
                "skills/technologies.json",
                lambda d, value=value: d["pgvector"].update(related_capabilities=[value]),
                "must be an implementation_capability",
            )
            for value in ["python", "technical-leadership", "data-visualization"]
        ],
        (
            "skills/technologies.json",
            lambda d: d["pgvector"].update(related_capabilities=["rag", "rag"]),
            "duplicate related capability",
        ),
        (
            "skills/ai.json",
            lambda d: d["rag"].update(related_capabilities=["rag"]),
            "self-related capability",
        ),
        (
            "skills/technologies.json",
            lambda d: d["python"].update(type="soft_skill"),
            "incompatible skill type",
        ),
        ("roles/ai-engineer.json", lambda d: d.pop("skill_options"), "skill_options"),
        ("roles/ai-engineer.json", lambda d: d.update(skill_options=[]), "skill_options"),
        (
            "roles/ai-engineer.json",
            lambda d: d["skill_options"][0].pop("priority"),
            "priority",
        ),
        (
            "roles/ai-engineer.json",
            lambda d: d["skill_options"][0].update(skill_id="unknown"),
            "must reference a role requirement",
        ),
        (
            "roles/ai-engineer.json",
            lambda d: d["skill_options"].append(d["skill_options"][0]),
            "duplicate skill option",
        ),
        (
            "roles/ai-engineer.json",
            lambda d: d["skill_options"][0].update(skill_id="technical-leadership"),
            "soft skill option",
        ),
        *[
            (
                "roles/ai-engineer.json",
                lambda d, value=value: d["skill_options"][0].update(priority=value),
                "priority",
            )
            for value in [0, 4, True, "1", None]
        ],
    ],
)
def test_invalid_skill_metadata_rejected(editable_data, filename, edit, expected):
    mutate(editable_data, filename, edit)
    with pytest.raises(CatalogError, match=expected):
        Catalog(editable_data)
