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
from roadmap_mcp.models import CatalogResult, Roadmap, SkillLimit, SkillsResponse
from roadmap_mcp.service import RoadmapService
from roadmap_mcp.skills_text import SkillsTextFormat, format_skills

Query = Annotated[str, Field(min_length=1, max_length=120)]
IncludeDescriptions = Annotated[
    bool,
    Field(
        strict=True, description="Include skill descriptions; false omits the description field."
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
            "list_catalog. For resume skills discovery, use get_skills with a role and optional "
            "industry and seniority. It returns role, industry, seniority, ordered categories "
            "as names, skill names grouped under P0, P1, and P2, and separate industry_context. "
            "Categories cover only returned skills after filters and limit and follow each "
            "role's explicit response_categories order, omitting empty categories. P0 means core, "
            "P1 supporting, and P2 specialized or optional. "
            "These map to source priorities 1, 2, and 3. "
            "Priorities are editorial role defaults, not job-specific rankings or measured hiring "
            "frequency. Industry additions use P2; seniority filters eligibility without changing "
            "role priorities. Technical roles use only the 23 technical categories; UX, product, "
            "and engineering management roles retain their applicable nontechnical categories. "
            "Industry concepts marked for experience are returned only in industry_context, "
            "with names and descriptions, outside skills and capability links. "
            "Context follows role, industry, and seniority and is independent of the skills limit; "
            "omitted industry returns an empty context list. Use it for evidenced experience "
            "bullets, never as entries in the resume Skills section. Named industry APIs, "
            "protocols, and standards remain eligible skills. Categories are available options. "
            "get_skills_text defaults to three lines: category names, skills with priorities, "
            "and industry_context names. Use output_format='detailed' for context descriptions, "
            "technology metadata, and optional skill "
            "descriptions. Families and selection groups provide selection hints, not exclusion "
            "rules; ecosystems and capability links never prove candidate experience. "
            "The resume generator computes a separate jd_priority from the job description "
            "and candidate evidence while preserving the MCP baseline priority. "
            "Match these options to the job description, verify the candidate's actual experience, "
            "remove irrelevant options, and then select roughly 15-25 evidenced skills as "
            "appropriate for the role. Put general practices in experience bullets unless "
            "the JD warrants listing them in the skills section. "
            "Do not copy the entire catalog into a resume. Categories vary with the selected role. "
            "get_roadmap is the compatibility endpoint for the full cumulative inventory using "
            "all three dimensions. Its response separates "
            "hard_skills and soft_skills, with named categories within each, and a separate "
            "industry_context list for domain concepts. Hard skills include technologies and "
            "learned methods; soft skills cover leadership and collaboration. "
            "Use get_skills to select entries for the resume Skills section. Demonstrate domain "
            "concepts and soft skills through evidenced experience bullets. Languages and "
            "frameworks are candidate stack choices. Include resume skills only when "
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
    def get_skills(
        role_name: Query,
        industry: Query | None = None,
        seniority_level: Query | None = None,
        limit: SkillLimit = 50,
        include_descriptions: IncludeDescriptions = False,
    ) -> SkillsResponse:
        """Return category names and skill names grouped by priority for a role.

        Only role_name is required. Accept names, IDs, and aliases from list_catalog.
        Return role, industry, seniority, categories [names], skills
        {P0: [names], P1: [names], P2: [names]}, and industry_context [{name, description}].
        P0 is core, P1 supporting, P2 optional.
        All three priority groups are present, even when empty. Categories follow the role's
        explicit response_categories order, omitting categories with no selected skills.
        Technical roles use only the 23-category taxonomy. Design, product, and management
        categories are allowed for their corresponding nontechnical roles. No industry categories.
        Categories are available options, not mandatory requirements. Excludes soft skills
        and experience-only industry concepts. Named APIs, protocols, and standards remain eligible.
        Preserve curated order within each priority; role options precede industry additions.
        Industry adds contextual options at P2 without changing existing role priorities.
        All role and industry options must belong to a category configured for the requested role.
        Omitted industry selects role options only. Omitted seniority includes all levels;
        a supplied level includes that level and below. limit is 1-50 (default 50).
        industry_context holds domain concepts for evidenced experience bullets, never Skills
        entries. It follows role/industry/seniority filters, ignores the skills limit and role
        category map, and is empty when industry is omitted. Context always includes descriptions.
        include_descriptions is accepted for compatibility; skill names have no descriptions.
        Use get_skills_text with output_format='detailed' for metadata and descriptions.
        Priorities are editorial baselines, not JD rankings or verified candidate experience.
        Unknown inputs and unsupported combinations return an error without substitution.
        """
        try:
            return SkillsResponse.from_result(
                service.get_skills(role_name, industry, seniority_level, limit)
            )
        except LookupError as error:
            raise ToolError(str(error)) from error

    @server.tool(annotations=READ_ONLY, structured_output=False)
    def get_skills_text(
        role_name: Query,
        industry: Query | None = None,
        seniority_level: Query | None = None,
        limit: SkillLimit = 50,
        include_descriptions: IncludeDescriptions = False,
        output_format: SkillsTextFormat = "compact",
    ) -> str:
        """Return the get_skills selection as compact or detailed plain text.

        Accept the same role, industry, seniority, and limit filters as get_skills.
        Compact output contains exactly three lines: categories: name, name, ...;
        skills: (name:P0), (name:P1), ...; industry_context: name, name, ... .
        Categories follow the role's configured order,
        omitting categories with no returned skills after filters and limit.
        Skills preserve selection order. P0 is core, P1 supporting, P2 specialized or optional.
        output_format='detailed' includes types, categories, families, ecosystems, selection
        groups, and capability links. include_descriptions=true adds descriptions only in
        detailed output. Detailed context always includes descriptions for writing experience
        bullets. Compact context contains names only. Domain concepts appear only in the separate
        context line/section, outside skill groups and capability links.
        Returns MCP text content without a JSON wrapper or structured output schema.
        Unknown inputs and unsupported combinations return the same errors as get_skills.
        """
        try:
            result = service.get_skills(
                role_name, industry, seniority_level, limit, include_descriptions
            )
        except LookupError as error:
            raise ToolError(str(error)) from error
        return format_skills(result, output_format)

    @server.tool(annotations=READ_ONLY)
    def get_roadmap(
        role_name: Query,
        industry: Query,
        seniority_level: Query,
        include_descriptions: IncludeDescriptions = True,
    ) -> Roadmap:
        """Compatibility endpoint for the complete cumulative hard and soft skill inventory.

        Prefer get_skills for curated resume discovery, category names, and baseline priorities.
        Accepts canonical names, IDs, or listed aliases, case-insensitively.
        Example: role_name='Backend Engineer', industry='Fintech', seniority_level='Senior'.
        Includes literal technology names such as Python, PostgreSQL, Redis, and Apache Kafka.
        Returns hard_skills and soft_skills, each a list of named categories with skills,
        and industry_context, a separate list of domain concepts for experience bullets.
        All three fields are always present; a field with no matches is an empty list.
        Empty categories are omitted. Category types are defined in the source catalog.
        include_descriptions defaults to true: skills contain name and description.
        Set include_descriptions=false to return each skill as {"name": "Python"}, omitting
        description entirely while preserving the categories and hard/soft sections.
        Technology alternatives are candidates for resume selection based on actual experience.
        Domain concepts are excluded from hard_skills and soft_skills and appear only in
        industry_context. Use them for evidenced experience bullets, never resume Skills entries.
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
