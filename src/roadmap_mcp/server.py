"""Thin MCP adapter; catalog and composition are independently testable."""

from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from roadmap_mcp import __version__
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


def create_server(catalog: Catalog) -> MCPServer:
    service = RoadmapService(catalog)
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
            "descriptions from get_roadmap results. Never invent achievements or certifications."
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

    @server.custom_route("/health", methods=["GET"])
    async def health(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return server
