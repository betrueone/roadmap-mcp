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
from roadmap_mcp.models import CatalogResult, Roadmap, SkillLimit, SkillsResult
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
            "industry and seniority. It returns a curated set of technology and implementation "
            "options with stable IDs, types, layers, categories, role-level priorities, "
            "technology_family, selection_group, technology_ecosystems, and related_capabilities "
            "as readable names. "
            "Prefer get_skills_text for compact model input: full skill names grouped by "
            "baseline priority and layer, with technologies grouped by ecosystems or categories. "
            "Joined ecosystem labels retain all curated associations, not required stacks. "
            "Use output_format='detailed' or get_skills for full technology metadata. "
            "Families group tools by purpose; optional selection groups hint at similar "
            "architectural positions. Neither imposes a one-per-group rule or proves "
            "interchangeability. Ecosystem hints connect language/runtime stacks and their "
            "frameworks or tools. Use them for coherent choices without restricting experienced "
            "candidates to one ecosystem; an empty list means no curated association. "
            "Keep complementary technologies when supported by experience. Capability links "
            "are canonical catalog names, not prerequisites or claims of candidate experience. "
            "Priority 1 means core, 2 supporting, and 3 specialized or optional. Priorities are "
            "editorial role defaults, not job-specific rankings or measured hiring frequency. "
            "The resume generator computes a separate jd_priority from the job description "
            "and candidate evidence while preserving the MCP baseline priority. "
            "Industry additions have priority 3. Alternatives are not a mandatory stack. "
            "Match these options to the job description, verify the candidate's actual experience, "
            "remove irrelevant options, and then select roughly 15-25 evidenced skills as "
            "appropriate for the role. Put general practices in experience bullets unless "
            "the JD warrants listing them in the skills section. "
            "Do not copy the entire catalog into a resume. Categories vary with the selected role. "
            "get_roadmap is the compatibility endpoint for the full cumulative inventory using "
            "all three dimensions. Its response separates "
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
    def get_skills(
        role_name: Query,
        industry: Query | None = None,
        seniority_level: Query | None = None,
        limit: SkillLimit = 50,
        include_descriptions: IncludeDescriptions = False,
    ) -> SkillsResult:
        """Discover curated technologies and implementation capabilities for resume selection.

        Only role_name is required. Accepts names, IDs, and aliases from list_catalog.
        Return role options (normally 30-50 for technical roles) with id, name, type, layer,
        category, priority, technology_family, selection_group, technology_ecosystems,
        and related_capabilities. Metadata uses readable names rather than identifiers.
        Core technologies include languages, runtimes, frameworks, SDKs, libraries,
        databases, extensions, streaming platforms, message brokers, test frameworks,
        CI/CD platforms, API query languages, APIs, operating systems, cloud platforms,
        cloud services, infrastructure, tools, protocols, and standards.
        Implementation capabilities identify applied work such as RAG, function calling,
        or transaction isolation.
        Nonengineering roles can also return professional_method entries. Excludes soft skills.
        Categories are supplied by the catalog and differ by role; there is no fixed category list.
        Priority is a role-level editorial default: 1 core, 2 supporting, 3 specialized or optional.
        The caller computes a separate jd_priority from the JD and verified candidate evidence;
        jd_priority is not part of this catalog response and does not overwrite its baseline.
        These are alternatives, not a required stack or verified candidate experience.
        technology_family groups technologies by purpose, without implying interchangeability
        or limiting results to one per family. Capabilities and methods have a null family.
        Optional selection_group hints at technologies filling similar architectural positions;
        it is not a hard exclusion rule. Null means no curated selection hint. Complementary
        tools can be retained together. Metadata never deduplicates tools automatically.
        technology_ecosystems lists curated language/runtime associations for coherent stack
        selection. It is nonexhaustive, permits multiple ecosystems, and never filters results
        or requires one stack. Empty means no curated association, not incompatibility.
        related_capabilities contains nonexhaustive canonical implementation-capability names
        from the full catalog, which may be outside this filtered response. Empty means no
        curated links. Links never add skills, change priorities, or prove proficiency.
        Omitted industry means role options only; an industry adds contextual options at priority 3.
        Omitted seniority means all levels; a supplied level includes that level and below.
        Counts describe catalog eligibility and the response limit, never JD or candidate fit.
        Preserve role priorities when an industry also references a role option. Sort by priority,
        then curated source order. Role options win ties over industry additions. limit is 1-50
        (default 50); available_count reports the eligible pool before this cap.
        include_descriptions defaults to false; true adds a short implementation description.
        The caller matches the JD, verifies candidate experience, and selects roughly 15-25
        final skills where appropriate; generic practices can be shown in experience bullets.
        Unknown inputs or unsupported combinations return an error without substitution.
        """
        try:
            return service.get_skills(
                role_name, industry, seniority_level, limit, include_descriptions
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
        """Return the same selection as get_skills, formatted as readable plain text.

        Only role_name is required. Accepts the same names, IDs, aliases, optional filters,
        limit (1-50, default 50), and include_descriptions (default false) as get_skills.
        Omitted industry selects role options only; omitted seniority includes all levels.
        A supplied seniority includes that level and below. output_format defaults to compact:
        full skill names grouped by baseline priority (P1/P2/P3) and layer (technologies,
        capabilities, methods). Technology rows group exact ecosystem associations, or use
        their category when none are curated. A '+' joins multiple ecosystem associations;
        associations are nonexhaustive hints, never mandatory stacks or exclusion rules.
        Each selected skill appears once; order within each group follows the catalog selection.
        Compact output omits types, families, selection groups, capability links, and counts.
        Set output_format='detailed' for categories, technology types, families, ecosystems,
        selection groups, and readable capability links. Use get_skills for structured data
        and eligibility counts. Both text formats match tests/test_tool.py and preserve selection.
        Descriptions, when requested, wrap at 100 columns; compact descriptions name their skill.
        Returns MCP text content without a JSON wrapper or structured output schema.
        Priorities are role defaults; the caller must match the JD and candidate experience.
        Unknown inputs and unsupported combinations return the same errors as get_skills.
        """
        return format_skills(
            get_skills(role_name, industry, seniority_level, limit, include_descriptions),
            output_format,
        )

    @server.tool(annotations=READ_ONLY)
    def get_roadmap(
        role_name: Query,
        industry: Query,
        seniority_level: Query,
        include_descriptions: IncludeDescriptions = True,
    ) -> Roadmap:
        """Compatibility endpoint for the complete cumulative hard and soft skill inventory.

        Prefer get_skills for curated resume discovery, skill types, and baseline priorities.
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
