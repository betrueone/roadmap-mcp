"""Thin MCP adapter; catalog and composition are independently testable."""

from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from roadmap_mcp import __version__
from roadmap_mcp.bullet_models import BulletCatalogResult, BulletCount, BulletsResult
from roadmap_mcp.bullet_text import format_bullets
from roadmap_mcp.bullets import BulletCatalog, BulletService
from roadmap_mcp.catalog import Catalog, LookupError
from roadmap_mcp.models import CatalogResult, Roadmap
from roadmap_mcp.service import RoadmapService

Query = Annotated[str, Field(min_length=1, max_length=120)]
IncludeDescriptions = Annotated[
    bool,
    Field(
        strict=True, description="Include skill descriptions; set false to return skill names only."
    ),
]
READ_ONLY = ToolAnnotations(
    read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
)


def create_server(catalog: Catalog, bullet_catalog: BulletCatalog | None = None) -> MCPServer:
    service = RoadmapService(catalog)
    bullet_service = BulletService(
        bullet_catalog
        if bullet_catalog is not None
        else BulletCatalog(catalog.directory / "bullets")
    )
    server = MCPServer(
        "Roadmap MCP",
        version=__version__,
        subscriptions=False,
        instructions=(
            "Discover supported roles, industries, seniority levels, and combinations with "
            "list_catalog. Use get_roadmap with all three dimensions. The response separates "
            "hard_skills and soft_skills, with named categories within each. Hard skills include "
            "technologies, learned methods, and industry knowledge; soft skills cover leadership "
            "and collaboration. Use hard skills for the resume Skills section and demonstrate "
            "soft skills through experience bullets. Languages and frameworks are "
            "candidate stack choices. Include resume skills only when "
            "supported by the user's experience. Set include_descriptions=false to omit skill "
            "descriptions from get_roadmap results. Use list_bullet_catalog to discover the "
            "separate bullet taxonomy and get_bullets to retrieve editorial baseline examples "
            "by role, optional industry, minimum seniority, and count. Seniority defaults to "
            "Junior and includes that level and higher. Omitted industry searches all industries. "
            "Prefer a requested industry, then fill shortfalls from other industries for the "
            "same role at or above the minimum seniority. Use get_bullets_text for the same "
            "selection as readable plain text with counts and evidence prompts. "
            "Results are deduplicated by text and preserve each bullet's original industry ID. "
            "Count is a maximum; available_count includes all unique industry fallback matches. "
            "Bullets are unverified examples, never "
            "candidate facts. Ask for the listed evidence_to_request and verify personal "
            "experience before tailoring them into a resume. "
            "Never invent achievements, metrics, or certifications."
        ),
    )

    @server.tool(annotations=READ_ONLY)
    def list_catalog() -> CatalogResult:
        """List roles, industries, seniority levels, aliases, and role/industry coverage."""
        return service.list_catalog()

    @server.tool(annotations=READ_ONLY)
    def get_roadmap(
        role_name: Query,
        industry: Query,
        seniority_level: Query,
        include_descriptions: IncludeDescriptions = True,
    ) -> Roadmap:
        """Return separate categorized hard and soft skills for the three inputs.

        Accepts canonical names, IDs, or listed aliases, case-insensitively.
        Example: role_name='Backend Engineer', industry='Fintech', seniority_level='Senior'.
        Includes literal technology names such as Python, PostgreSQL, Redis, and Apache Kafka.
        Returns hard_skills and soft_skills, each a list of named categories with skills.
        Both sections are always present; a section with no matching skills is an empty list.
        Empty categories are omitted. Category types are defined in the source catalog.
        include_descriptions defaults to true: skills contain name and description.
        Set include_descriptions=false to return each skill as {"name": "Python"}, omitting
        description entirely while preserving the categories and hard/soft sections.
        Technology alternatives are candidates for resume selection based on actual experience.
        Unknown inputs and unsupported combinations return an error; there is no fallback.
        """
        try:
            return service.get_roadmap(
                role_name, industry, seniority_level, include_descriptions=include_descriptions
            )
        except LookupError as error:
            raise ToolError(str(error)) from error

    @server.tool(annotations=READ_ONLY)
    def list_bullet_catalog() -> BulletCatalogResult:
        """List supported bullet roles, industries, seniorities, aliases, coverage, and count.

        Bullet coverage differs from the skill roadmap catalog. Use this tool to discover
        exact baseline IDs and aliases. Bullet examples are editorial baselines for tailoring.
        """
        return bullet_service.list_bullet_catalog()

    @server.tool(annotations=READ_ONLY)
    def get_bullets(
        role_name: Query,
        industry: Query | None = None,
        seniority_level: Query | None = "junior",
        count: BulletCount = 5,
    ) -> BulletsResult:
        """Return unique resume bullet baselines, preferring the requested industry.

        Accepts bullet catalog IDs, names, and aliases, case-insensitively. Example:
        role_name='Backend Engineer', industry='Fintech', seniority_level='Senior', count=5.
        Only role_name is required. Omit industry or pass null to search all industries.
        seniority_level defaults to junior; null also uses junior. Match that level or above:
        Senior includes Senior and Staff, and Junior includes all levels. Match role exactly.
        Count must be an integer from 1 to 100 (default 5).
        Return requested-industry matches first. Fill shortfalls from other industries,
        preserving the minimum seniority. Keep datasource order within each group.
        Deduplicate bullet text ignoring case and extra whitespace; requested industry wins.
        Each bullet retains its original industry_id, including fallback matches.
        available_count is the unique pool across industries at or above the minimum seniority.
        Return fewer than count only if that pool is exhausted; an empty pool returns no bullets.
        Unknown dimensions return an error pointing to list_bullet_catalog.
        Each bullet contains its ID, role/industry IDs, seniority, focus, text,
        and evidence prompts.
        Tailor only after verifying the person's actual work; never assert fabricated metrics.
        """
        try:
            return bullet_service.get_bullets(role_name, industry, seniority_level, count)
        except LookupError as error:
            raise ToolError(str(error)) from error

    @server.tool(annotations=READ_ONLY, structured_output=False)
    def get_bullets_text(
        role_name: Query,
        industry: Query | None = None,
        seniority_level: Query | None = "junior",
        count: BulletCount = 5,
    ) -> str:
        """Return the same selection as get_bullets, formatted as readable plain text.

        Only role_name is required. industry defaults to all industries, seniority_level
        defaults to junior and includes that level or higher, and count defaults to 5 (1–100).
        Prioritize a requested industry, fill shortfalls across industries, and deduplicate text.
        Output includes a title, counts, numbered bullets, seniority, fallback industry labels,
        and evidence prompts, matching the readable local test script. Returns MCP text content
        without a JSON wrapper. Unknown inputs return the same errors as get_bullets.
        """
        return format_bullets(get_bullets(role_name, industry, seniority_level, count))

    @server.custom_route("/health", methods=["GET"])
    async def health(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return server
