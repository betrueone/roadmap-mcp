import json
import shutil
import subprocess
import sys
from itertools import product

import pytest
from mcp import Client
from pydantic import ValidationError

from roadmap_mcp.bullet_models import BulletsResult
from roadmap_mcp.bullet_text import format_bullets
from roadmap_mcp.bullets import BulletCatalog, BulletService
from roadmap_mcp.catalog import CatalogError, LookupError
from roadmap_mcp.server import create_server

from .conftest import DATA_DIR

ROOT = DATA_DIR.parent
BULLET_FIELDS = {
    "id",
    "role_id",
    "industry_id",
    "seniority",
    "focus",
    "bullet",
    "evidence_to_request",
}


@pytest.fixture(scope="module")
def bullet_catalog():
    return BulletCatalog(DATA_DIR / "bullets")


@pytest.fixture(scope="module")
def bullet_service(bullet_catalog):
    return BulletService(bullet_catalog)


def edit_first_bullet(directory, edit):
    path = directory / "bullets/bullets.jsonl"
    rows = path.read_text().splitlines()
    first = json.loads(rows[0])
    edit(first)
    rows[0] = json.dumps(first)
    path.write_text("\n".join(rows) + "\n")


def write_bullets(directory, rows):
    (directory / "bullets/bullets.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n"
    )
    manifest_path = directory / "bullets/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["bullet_count"] = len(rows)
    manifest_path.write_text(json.dumps(manifest))


def test_reference_import_keeps_only_tailoring_fields_and_preserves_content(bullet_catalog):
    references = ROOT / "reference"
    original = json.loads((references / "bullets.json").read_text())
    expected = [{key: row[key] for key in BULLET_FIELDS} for row in original]
    stored = [
        json.loads(line) for line in (DATA_DIR / "bullets/bullets.jsonl").read_text().splitlines()
    ]
    assert stored == expected
    assert [row.model_dump(mode="json") for row in bullet_catalog.bullets] == expected
    manifest = json.loads((DATA_DIR / "bullets/manifest.json").read_text())
    assert set(manifest) == {
        "dataset",
        "version",
        "role_count",
        "industry_count",
        "seniority_levels",
        "bullet_count",
    }
    assert {file.name for file in (DATA_DIR / "bullets").iterdir()} == {
        "catalog.json",
        "manifest.json",
        "bullets.jsonl",
    }
    assert len(bullet_catalog.bullets) == 2040
    assert len(bullet_catalog.roles) == 17
    assert len(bullet_catalog.industries) == 20
    assert len(bullet_catalog.by_combination) == 17 * 20 * 4


def test_discovery_uses_bullet_taxonomy_and_lists_actual_coverage(bullet_service):
    result = bullet_service.list_bullet_catalog()
    assert result.bullet_count == 2040
    assert "product-engineer" in {role.id for role in result.roles}
    assert "igaming" in {industry.id for industry in result.industries}
    assert {role.id for role in result.roles}.isdisjoint({"qa-engineer", "data-analyst"})
    assert [level.id for level in result.seniority_levels] == ["junior", "mid", "senior", "staff"]
    assert all(len(coverage.industry_ids) == 20 for coverage in result.coverage)
    assert set(result.model_dump()) == {
        "roles",
        "industries",
        "seniority_levels",
        "coverage",
        "bullet_count",
    }


def test_all_combinations_prefer_industry_and_respect_minimum_seniority(
    bullet_service, bullet_catalog
):
    industry_counts = {"junior": 6, "mid": 5, "senior": 3, "staff": 1}
    for role, industry, level in product(
        bullet_catalog.roles, bullet_catalog.industries, bullet_catalog.levels
    ):
        result = bullet_service.get_bullets(role, industry, level, count=100)
        assert result.role.id == role
        assert result.industry.id == industry
        assert result.seniority_level.id == level
        assert result.requested_count == 100
        assert result.available_count == industry_counts[level] * 20
        assert result.returned_count == min(100, result.available_count)
        assert len(result.bullets) == len({row.id for row in result.bullets})
        assert len(result.bullets) == len({row.bullet.casefold() for row in result.bullets})
        assert all(row.industry_id == industry for row in result.bullets[: industry_counts[level]])
        assert all(row.industry_id != industry for row in result.bullets[industry_counts[level] :])
        for row in result.bullets:
            assert row.role_id == role
            assert bullet_catalog.levels[row.seniority].rank >= bullet_catalog.levels[level].rank
            assert row.evidence_to_request


@pytest.mark.parametrize(
    "canonical, aliases",
    [
        (
            ("backend-engineer", "fintech-payments", "senior"),
            ("  BACKEND   DEVELOPER ", "Financial Technology", "Sr."),
        ),
        (
            ("fullstack-engineer", "ecommerce-retail", "mid"),
            ("Full Stack Engineer", "E-commerce", "mid level"),
        ),
        (
            ("ai-llm-engineer", "b2b-saas", "junior"),
            ("AI Engineer", "SaaS", "entry level"),
        ),
    ],
)
def test_aliases_resolve_to_reference_ids(bullet_service, canonical, aliases):
    assert bullet_service.get_bullets(*canonical) == bullet_service.get_bullets(*aliases)


def test_count_is_a_limit_with_stable_order_and_explicit_shortfalls(bullet_service):
    args = ("Backend Engineer", "Fintech", "Senior")
    first = bullet_service.get_bullets(*args, count=1)
    full = bullet_service.get_bullets(*args)
    assert full.requested_count == 5
    assert full.returned_count == 5
    assert full.available_count == 60
    assert first.requested_count == first.returned_count == 1
    assert first.available_count == 60
    assert first.bullets == full.bullets[:1]
    assert bullet_service.get_bullets(*args) == full
    exact = bullet_service.get_bullets(*args, count=3)
    assert all(row.industry_id == "fintech-payments" for row in exact.bullets)
    assert exact.bullets == full.bullets[:3]
    assert {row.seniority for row in exact.bullets} == {"senior", "staff"}
    assert all(row.industry_id != "fintech-payments" for row in full.bullets[3:])


def test_omitted_and_null_filters_default_to_all_industries_and_junior(
    bullet_service, bullet_catalog
):
    result = bullet_service.get_bullets("Backend Engineer", count=100)
    assert result.industry is None
    assert result.seniority_level.id == "junior"
    assert result.available_count == 120
    assert result.returned_count == 100
    assert (
        result.bullets
        == [row for row in bullet_catalog.bullets if row.role_id == "backend-engineer"][:100]
    )
    assert bullet_service.get_bullets("Backend Engineer", None, None, 100) == result
    preferred = bullet_service.get_bullets("Backend Engineer", industry="Fintech", count=6)
    assert preferred.seniority_level.id == "junior"
    assert all(row.industry_id == "fintech-payments" for row in preferred.bullets)
    assert {row.seniority for row in preferred.bullets} == {"junior", "mid", "senior", "staff"}


@pytest.mark.parametrize(
    "minimum, included, available",
    [
        ("Junior", {"junior", "mid", "senior", "staff"}, 120),
        ("Mid-level", {"mid", "senior", "staff"}, 100),
        ("Senior", {"senior", "staff"}, 60),
        ("Staff", {"staff"}, 20),
    ],
)
def test_explicit_minimum_without_industry_includes_equal_and_higher_levels(
    bullet_service, minimum, included, available
):
    result = bullet_service.get_bullets("Backend Engineer", seniority_level=minimum, count=100)
    assert result.industry is None
    assert result.available_count == available
    assert result.returned_count == min(100, available)
    assert {row.seniority for row in result.bullets} == included
    assert all(row.role_id == "backend-engineer" for row in result.bullets)


@pytest.mark.parametrize("count", [0, -1, 101, True, False, 1.5, "2", None])
def test_service_rejects_invalid_counts(bullet_service, count):
    with pytest.raises(ValidationError):
        bullet_service.get_bullets("Backend Engineer", "Fintech", "Senior", count)


@pytest.mark.parametrize(
    "args, dimension",
    [
        (("Data Analyst", "Fintech", "Senior"), "role"),
        (("Backend Engineer", "unknown", "Senior"), "industry"),
        (("Backend Engineer", "Fintech", "principal"), "seniority"),
    ],
)
def test_unknown_inputs_point_to_bullet_discovery(bullet_service, args, dimension):
    with pytest.raises(LookupError, match=f"Unknown bullet {dimension}.*list_bullet_catalog"):
        bullet_service.get_bullets(*args)


@pytest.mark.parametrize("remove_all_industries", [False, True])
def test_empty_industry_uses_fallback_and_empty_role_seniority_returns_no_bullets(
    editable_data, remove_all_industries
):
    path = editable_data / "bullets/bullets.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows = [
        row
        for row in rows
        if not (
            row["role_id"] == "backend-engineer"
            and row["seniority"] in {"senior", "staff"}
            and (remove_all_industries or row["industry_id"] == "fintech-payments")
        )
    ]
    write_bullets(editable_data, rows)
    result = BulletService(BulletCatalog(editable_data / "bullets")).get_bullets(
        "Backend Engineer", "Fintech", "Senior"
    )
    if remove_all_industries:
        assert result.bullets == []
        assert result.available_count == result.returned_count == 0
        assert "No matching bullets." in format_bullets(result)
    else:
        assert result.returned_count == 5
        assert result.available_count == 57
        assert all(row.industry_id != "fintech-payments" for row in result.bullets)
        assert all(
            row.role_id == "backend-engineer" and row.seniority in {"senior", "staff"}
            for row in result.bullets
        )


def test_fallback_deduplicates_text_and_keeps_requested_industry_copy(editable_data):
    rows = [
        json.loads(line)
        for line in (editable_data / "bullets/bullets.jsonl").read_text().splitlines()
    ]
    eligible = [
        row for row in rows if (row["role_id"], row["seniority"]) == ("backend-engineer", "senior")
    ]
    primary = [row for row in eligible if row["industry_id"] == "fintech-payments"]
    earlier = [row for row in eligible if row["industry_id"] == "b2b-saas"]
    later = next(row for row in eligible if row["industry_id"] == "banking-lending")
    earlier[0]["bullet"] = "  ".join(primary[0]["bullet"].upper().split())
    later["bullet"] = " \t ".join(earlier[1]["bullet"].upper().split())
    write_bullets(editable_data, rows)
    service = BulletService(BulletCatalog(editable_data / "bullets"))
    full = service.get_bullets("Backend Engineer", "Fintech", "Senior", count=100)
    limited = service.get_bullets("Backend Engineer", "Fintech", "Senior", count=5)
    assert full.returned_count == full.available_count == 58
    assert limited.returned_count == 5
    assert limited.available_count == 58
    assert limited.bullets == full.bullets[:5]
    assert [row.id for row in full.bullets[:2]] == [row["id"] for row in primary]
    ids = {row.id for row in full.bullets}
    assert earlier[0]["id"] not in ids
    assert later["id"] not in ids
    assert earlier[1]["id"] in ids
    assert len({" ".join(row.bullet.split()).casefold() for row in full.bullets}) == 58


def test_duplicate_primary_text_triggers_fallback_after_deduplication(editable_data):
    rows = [
        json.loads(line)
        for line in (editable_data / "bullets/bullets.jsonl").read_text().splitlines()
    ]
    primary = [
        row
        for row in rows
        if (row["role_id"], row["industry_id"], row["seniority"])
        == ("backend-engineer", "fintech-payments", "senior")
    ]
    primary[1]["bullet"] = primary[0]["bullet"]
    write_bullets(editable_data, rows)
    service = BulletService(BulletCatalog(editable_data / "bullets"))
    result = service.get_bullets("Backend Engineer", "Fintech", "Senior", count=3)
    assert result.returned_count == 3
    assert result.available_count == 59
    assert result.bullets[0].id == primary[0]["id"]
    assert result.bullets[1].industry_id == "fintech-payments"
    assert result.bullets[1].seniority == "staff"
    assert result.bullets[2].industry_id != "fintech-payments"
    assert len({row.bullet for row in result.bullets}) == 3


@pytest.mark.parametrize(
    "changes, expected",
    [
        ({"role_id": "unknown"}, "unknown role"),
        ({"industry_id": "unknown"}, "unknown industry"),
        ({"seniority": "principal"}, "unknown seniority"),
        ({"bullet": " "}, "bullet"),
        ({"focus": ""}, "focus"),
        ({"id": "bad id"}, "id"),
        ({"onet_soc_reference": "15-1252.00"}, "Extra inputs"),
        ({"supporting_occupation_source": "https://example.com"}, "Extra inputs"),
        ({"industry_classification_source": "https://example.com"}, "Extra inputs"),
        ({"origin": "unused metadata"}, "Extra inputs"),
        ({"evidence_to_request": []}, "evidence_to_request"),
    ],
)
def test_invalid_baselines_fail_before_serving(editable_data, changes, expected):
    edit_first_bullet(editable_data, lambda row: row.update(changes))
    with pytest.raises(CatalogError, match=expected):
        BulletCatalog(editable_data / "bullets")


def test_duplicate_bullet_ids_rejected(editable_data):
    path = editable_data / "bullets/bullets.jsonl"
    text = path.read_text()
    path.write_text(text + text.splitlines()[0] + "\n")
    with pytest.raises(CatalogError, match="Duplicate bullet ID"):
        BulletCatalog(editable_data / "bullets")


def test_manifest_mismatch_rejected(editable_data):
    path = editable_data / "bullets/manifest.json"
    manifest = json.loads(path.read_text())
    manifest["bullet_count"] += 1
    path.write_text(json.dumps(manifest))
    with pytest.raises(CatalogError, match="manifest counts"):
        BulletCatalog(editable_data / "bullets")


def test_ambiguous_aliases_rejected(editable_data):
    path = editable_data / "bullets/catalog.json"
    taxonomy = json.loads(path.read_text())
    taxonomy["roles"][0]["aliases"].append("Backend Engineer")
    path.write_text(json.dumps(taxonomy))
    with pytest.raises(CatalogError, match="Ambiguous bullet role alias"):
        BulletCatalog(editable_data / "bullets")


def test_malformed_jsonl_reports_line_and_duplicate_keys(editable_data):
    path = editable_data / "bullets/bullets.jsonl"
    path.write_text('\n{"id":"a","id":"b"}\n')
    with pytest.raises(CatalogError, match="bullets.jsonl:2:.*Duplicate JSON key"):
        BulletCatalog(editable_data / "bullets")


def test_missing_datasource_rejected(tmp_path):
    with pytest.raises(CatalogError, match="bullets/catalog.json"):
        BulletCatalog(tmp_path)


def test_import_is_reproducible_and_invalid_import_preserves_runtime_files(editable_data, tmp_path):
    from scripts.import_bullets import import_bullets

    destination = editable_data / "bullets"
    before = {file.name: file.read_bytes() for file in destination.iterdir()}
    (destination / "sources.json").write_text("[]\n")
    import_bullets(ROOT / "reference", editable_data)
    assert {file.name: file.read_bytes() for file in destination.iterdir()} == before
    invalid = tmp_path / "reference"
    invalid.mkdir()
    for name in ("roles.json", "industries.json", "manifest.json"):
        shutil.copyfile(ROOT / "reference" / name, invalid / name)
    (invalid / "bullets.jsonl").write_text("{broken}\n")
    with pytest.raises(CatalogError, match="bullets.jsonl:1"):
        import_bullets(invalid, editable_data)
    assert {file.name: file.read_bytes() for file in destination.iterdir()} == before


def test_validate_cli_reports_bullets_and_rejects_corruption(editable_data):
    command = [sys.executable, "-m", "roadmap_mcp", "validate", "--data-dir", str(editable_data)]
    valid = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(valid.stdout)["bullet_catalog"] == {
        "roles": 17,
        "industries": 20,
        "seniority_levels": 4,
        "bullets": 2040,
        "dataset_version": "1.0.0",
    }
    edit_first_bullet(editable_data, lambda row: row.update(bullet=""))
    invalid = subprocess.run(command, capture_output=True, text=True)
    assert invalid.returncode == 1
    assert "Catalog validation failed" in invalid.stderr
    assert "bullet" in invalid.stderr


async def test_mcp_bullet_discovery_schema_and_structured_results(catalog):
    async with Client(create_server(catalog)) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
        tool = tools["get_bullets"]
        assert tool.annotations.read_only_hint
        assert tool.annotations.destructive_hint is False
        assert tool.output_schema
        count = tool.input_schema["properties"]["count"]
        assert count["type"] == "integer"
        assert count["minimum"] == 1 and count["maximum"] == 100 and count["default"] == 5
        assert tool.input_schema["required"] == ["role_name"]
        assert tool.input_schema["properties"]["industry"]["default"] is None
        assert tool.input_schema["properties"]["seniority_level"]["default"] == "junior"
        discovery = await client.call_tool("list_bullet_catalog")
        assert not discovery.is_error
        assert discovery.structured_content["bullet_count"] == 2040
        result = await client.call_tool(
            "get_bullets",
            {
                "role_name": "Backend Engineer",
                "industry": "Fintech",
                "seniority_level": "Senior",
                "count": 5,
            },
        )
        assert not result.is_error
        payload = result.structured_content
        assert json.loads(result.content[0].text) == payload
        parsed = BulletsResult.model_validate(payload)
        assert parsed.available_count == 60
        assert parsed.returned_count == len(parsed.bullets) == 5
        assert [row.industry_id for row in parsed.bullets[:3]] == [
            "fintech-payments",
            "fintech-payments",
            "fintech-payments",
        ]
        assert all(row.industry_id != "fintech-payments" for row in parsed.bullets[3:])
        assert all(set(row) == BULLET_FIELDS for row in payload["bullets"])
        invalid = await client.call_tool(
            "get_bullets",
            {
                "role_name": "Data Analyst",
                "industry": "Fintech",
                "seniority_level": "Senior",
            },
        )
        assert invalid.is_error
        assert "list_bullet_catalog" in invalid.content[0].text


@pytest.mark.parametrize("tool_name", ["get_bullets", "get_bullets_text"])
async def test_mcp_rejects_invalid_bullet_arguments(catalog, tool_name):
    async with Client(create_server(catalog)) as client:
        base = {"role_name": "Backend Engineer", "industry": "Fintech", "seniority_level": "Senior"}
        for args in [
            {key: value for key, value in base.items() if key != "role_name"},
            {**base, "role_name": ""},
            {**base, "industry": 123},
            {**base, "industry": ""},
            {**base, "seniority_level": ""},
            {**base, "seniority_level": "x" * 121},
            *[{**base, "count": count} for count in [0, -1, 101, True, 1.5, "2", None]],
        ]:
            result = await client.call_tool(tool_name, args)
            assert result.is_error, args


@pytest.mark.parametrize("optional", [{}, {"industry": None, "seniority_level": None}])
async def test_mcp_optional_filters_use_defaults(catalog, optional):
    async with Client(create_server(catalog)) as client:
        result = await client.call_tool(
            "get_bullets", {"role_name": "Backend Engineer", **optional}
        )
        assert not result.is_error
        parsed = BulletsResult.model_validate(result.structured_content)
        assert parsed.industry is None
        assert parsed.seniority_level.id == "junior"
        assert parsed.available_count == 120
        assert parsed.returned_count == 5


@pytest.mark.parametrize(
    "filters, title, available",
    [
        ({}, "All industries | Junior and above", 120),
        (
            {"industry": "Fintech", "seniority_level": "Senior"},
            "Fintech & Payments | Senior and above",
            60,
        ),
    ],
)
async def test_mcp_plain_text_tool_matches_structured_selection(catalog, filters, title, available):
    async with Client(create_server(catalog)) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
        tool = tools["get_bullets_text"]
        assert tool.output_schema is None
        assert tool.annotations.read_only_hint
        assert tool.input_schema["required"] == ["role_name"]
        assert tool.input_schema["properties"]["seniority_level"]["default"] == "junior"
        args = {"role_name": "Backend Engineer", "count": 5, **filters}
        structured = await client.call_tool("get_bullets", args)
        text = await client.call_tool("get_bullets_text", args)
        assert not text.is_error
        assert text.structured_content is None
        assert len(text.content) == 1
        assert text.content[0].type == "text"
        content = text.content[0].text
        assert content == format_bullets(
            BulletsResult.model_validate(structured.structured_content)
        )
        assert title in content
        assert f"5 returned / 5 requested / {available} available" in content
        assert "1. " in content
        assert "Evidence to verify:" in content
        assert "Seniority:" in content
        if filters:
            assert content.count("(fallback)") == 2
        invalid = await client.call_tool("get_bullets_text", {"role_name": "unknown"})
        assert invalid.is_error
        assert "list_bullet_catalog" in invalid.content[0].text
