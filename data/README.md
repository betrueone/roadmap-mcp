# Skill catalog curation

This catalog supplies skills a candidate can support with concrete work. Role, industry,
and seniority determine relevance; they cannot establish that a person implemented a skill.
Technology stacks remain alternatives to select from using the candidate's experience.

`get_skills` is the primary discovery endpoint. Role files explicitly curate 31-47 options for
technical roles in `skill_options`, each with a role-level priority. The response identifies
named technologies and implementation capabilities separately through `layer` and `type`.
Nonengineering methods remain available as `professional_method`; soft skills are excluded.
The larger `requirements` inventory remains available through the compatible `get_roadmap` tool.

All 194 entries in `skills/industries.json` have `resume_section: "experience"`. These are domain
concepts for writing evidenced experience bullets, not Skills-section entries. Both `get_skills`
and `get_roadmap` return matched concepts separately in `industry_context`, filtered by role,
industry, and seniority. The field is outside skill priorities, counts, limits, and category maps.
It is empty in role-only discovery. Structured `get_skills` context always includes names and
descriptions; `get_roadmap` respects `include_descriptions` for context as well as skills.
Compact text has a third `industry_context` line; detailed text has a separate context section.

The seven named industry standards/protocols (LTI, ISO 20022, TM Forum Open APIs, HLS, OPC UA,
RESO Web API, and DCAT) now live in `skills/technologies.json`, which contains all 183 named
technologies. Their IDs, categories, and industry mappings are preserved. Concrete APIs such as
Stripe API also remain eligible Skills entries. Context never proves candidate experience.

Other definitions default to `resume_section: "skills"`. Catalog validation rejects
experience-only concepts in curated role `skill_options`; they remain valid requirements.
Capability links retain their canonical IDs in source data but omit experience-only targets
from Skills output. This prevents concept names from leaking back through technology metadata.

## Inclusion rules

- Keep named languages, frameworks, tools, protocols, and standards when relevant to the role.
- Keep applied concepts when they identify a distinct implementation, operational procedure,
  analysis, or deliverable. A concept does not need to be a product name to qualify.
- Use a name that conveys the capability on its own: clients can omit descriptions.
- Describe observable work: what is implemented, its constraints or failure cases, and how
  someone could demonstrate it through code, configuration, tests, measurements, or artifacts.
- Remove generic prerequisites and umbrella headings when more specific entries already cover
  the useful work. Avoid listing both an umbrella and its component skills as separate signals.
- Retain role-specific methods for design, product, analytics, and management. Evidence can be
  a research study, analysis, acceptance criteria, or a budget model as appropriate to the role.
- Keep interpersonal skills in the existing soft-skill categories; demonstrate them through
  experience examples. Do not turn them into invented implementation claims.

## Examples from this revision

| Previous entry | Curated treatment |
| --- | --- |
| RESTful APIs | Keep; describe resource endpoints, pagination, validation, and HTTP semantics. |
| OAuth | Name OAuth 2.0 explicitly; describe authorization code, PKCE, scopes, and token lifecycle. |
| OpenID | Name OpenID Connect explicitly; describe sign-in and ID token validation. |
| API design | Remove overlapping heading; retain RESTful APIs, OpenAPI, API versioning, and contract testing. |
| System design | Remove broad heading; retain scoped capabilities such as regional failover, tenant isolation, and transactional outboxes. |
| Automated testing | Separate unit testing and integration testing with distinct boundaries and failure cases. |
| Observability | Select logging, metrics, and tracing for service roles; browser telemetry, mobile crash diagnostics, or model tracing for the relevant application role. |
| HTTP fundamentals, generic debugging, linear algebra | Remove prerequisite topics from the candidate skill inventory. |
| Transactions and concurrency | Specify transaction isolation and locking, including concurrent-update failures. |
| Application caching | Specify cache invalidation, expiration, and stampede protection. |
| Commerce domain concepts | Retain product catalog and order modeling as experience context. |

The initial curation pass retired 25 broad or overlapping entries, introduced 8 scoped implementation
entries, and refined 68 existing names or descriptions. It retained all 20 roles, 15 industries,
4 seniority levels, and the original 39 categories. Typed discovery below adds 5 technologies
and 4 categories, bringing the current inventory to 605 skills in 43 categories.
Source mappings remain explicit and cumulative. When
overlapping requirements merge, keep the earliest existing minimum seniority. Changes to skill
names are visible to clients, including clients requesting names only; the response schema stays
the same for `get_roadmap`.

## Typed discovery and priorities

Every stored skill now requires `type`. Named products, languages, protocols, and standards
have an explicit technology type; applied engineering work uses `implementation_capability`.
The server does not guess a type from names. Categories remain configurable source data,
and each role returns only the categories of its selected options.

Use specific types where the engineering identity warrants them:

| Technologies | Type |
| --- | --- |
| Node.js | `runtime` |
| Apache Kafka | `event_streaming_platform` |
| RabbitMQ | `message_broker` |
| pytest, JUnit, Jest, Vitest, XCTest | `test_framework` |
| GitHub Actions, GitLab CI, Jenkins | `ci_cd_platform` |
| GraphQL | `api_query_language` |

GraphQL's family is `API Query Languages`; the three CI/CD systems share `CI/CD Platforms`.
The complete review also distinguishes APIs (`api`), operating systems (`operating_system`),
cloud platforms (`cloud_platform`), and hosted services (`cloud_service`), and corrects
React, gRPC, Delta Lake, OpenTelemetry, Apple frameworks, Cypress, Locust, and HLS.
These types are shared across roles. Existing generic types remain valid for other technologies.
The public `get_skills` type enum includes these specific values; clients with a copied enum
must accept them. `get_roadmap` now returns domain concepts separately in `industry_context`.

Each role must define an ordered `response_categories` list in its JSON file. This map controls
category order in `get_skills` and compact `get_skills_text` output. Technical roles use only
relevant names from the 23-category response taxonomy in `src/roadmap_mcp/skill_categories.py`.
UX Designer, Product Manager, and Engineering Manager may also use their applicable design,
product, and management categories. Data Analyst may include Product Management; QA Engineer
may include Engineering Management for their curated methods. Legacy industry labels are not
allowed in role maps. Include categories covering every curated option and every Skills-eligible
direct role/industry assignment within the permitted taxonomy. All role and
industry options must belong to the role's map to be selected; apply this check before the
skill limit. Return category names without skill counts and omit categories with no selected
skills. Catalog validation rejects missing, empty, duplicate, unknown, or incomplete maps.
Shared industry defaults can still be excluded by role relevance. Skills-eligible technologies
and applied capabilities require a permitted projection. Experience-only domain concepts,
including modeling and disclosure concepts, bypass Skills category maps and appear only in
`industry_context`.

Every role also authors a nonempty `required_categories` list. These categories must belong to
its response map and have curated role-only coverage across the full seniority inventory.
Startup rejects duplicates and uncovered required categories. Seniority and result-limit filters
can omit them; they are catalog coverage requirements, not a candidate proficiency checklist.
Third-Party Integrations and other contextual categories can remain optional.

The response taxonomy now separates Web Platform and Mobile Development, broadens the shared
UI label to Frontend & UI Engineering, and identifies Backend Frameworks & Runtimes accurately.
Component libraries and design tokens use the shared UI category; Hilt uses Architecture & System
Design. Monetary and healthcare record modeling use Data Modeling & Transformation, client event
instrumentation uses BI & Analytics, and financial reconciliation uses Data Quality & Governance.
Fraud signal integration uses Security & Authentication; model training keeps its AI/ML category.
Source category ownership and stable skill IDs are unchanged.

Each role has an independently curated `skill_options` list referencing a subset of its
`requirements`. Priority 1 marks core options, 2 supporting options, and 3 specialized or
optional options. These are editorial defaults for that role. They do not measure market share,
job-posting frequency, or the importance of a skill to a particular vacancy. Alternative stacks
may coexist; priority does not imply that the candidate must know every option. Keep priorities
independent of seniority and justify relevance through the role's work.

Curate the role itself before considering industry context. Avoid filling a numerical quota
with generic topics. A role-only discovery call returns its explicit subset across all levels.
An optional seniority filter respects existing minimum thresholds. An optional industry adds
contextual skills at priority 3 without changing role defaults. A skill excluded by the role's
seniority threshold cannot reappear through an industry mapping. The default response caps at
50 entries and reports the eligible count before the cap; narrower filters can return fewer.

This update adds five technologies to fill specific gaps: OpenAI SDK for provider integration,
Pydantic for typed validation, LangGraph for stateful workflow orchestration, pgvector for
PostgreSQL vector retrieval, and Ragas for executable LLM evaluation. It reuses existing languages,
frameworks, databases, infrastructure, and capabilities elsewhere. The review's example list is
illustrative; it is not imported as a fixed stack or as the complete catalog for every role.
Names such as RAG, function calling, structured outputs, agent workflows, and fine-tuning identify
the capability; descriptions retain implementation detail and failure handling.

The AI Engineer profile retains its original 41 options and adds RESTful APIs and data access
governance for 43 options. Its named provider, API, validation, vector
storage, and container implementation choices use P2 after the complete review. Its priority-1 capabilities are RAG, function
calling, structured outputs, and LLM evaluation. Embeddings, vector search, document ingestion,
prompt engineering, and agent workflows use priority 2. General unit and integration testing
use priority 3, alongside specialized fairness, privacy, and infrastructure cost capabilities;
named test tools remain separate options. These are editorial choices for this baseline role,
not universal requirements or a fixed resume template. A job description can change downstream
priorities without changing the MCP baseline.
The resume generator should retain `priority` and compute its own separate `jd_priority` using
the JD and verified candidate evidence. No JD ranking is computed or returned by this server.
The review's comparison table remains illustrative; it is not imported into role mappings.

The Backend Engineer baseline has 47 options: 31 named technologies and 16 implementation
capabilities, including structured logging for baseline observability. The complete review moved
the existing PHP and Ruby options from e-commerce
mappings into the generic backend and full-stack profiles at P3. Python, Java, Go, JavaScript, TypeScript, and Node.js use P2 to represent relevant
stack alternatives pending JD and candidate selection. C# and Rust retain their specialized P3
defaults. Transaction isolation and locking and role-based/resource-level authorization move
to P2. RESTful APIs, relational schema design, session/token authentication, unit testing, and
integration testing remain P1. Database indexing and query tuning remain P2, an editorial choice
within the review's P1-P2 range; a performance-focused JD can promote them downstream.
The full review preserves all 605 skill IDs. It adjusts role priorities, selected entry-level
thresholds, and a few industry/category mappings; see [the complete review](REVIEW.md).
Counts represent catalog eligibility before/after the limit, not JD relevance or candidate fit.

## Technology families and capability links

All 183 existing technologies, including industry-specific standards, have an authored
`technology_family` and `related_capabilities` list. No technologies or capabilities were added
or removed for this refinement. Family and selection-group values are authored, readable names.
Stored capability references use existing hyphenated skill IDs for validation; `get_skills`
resolves them to canonical capability names. No metadata is guessed at request time.

- Families describe a shared engineering purpose, not identical behavior, dependencies, or
  mutual exclusion. Reuse an existing family when the purpose matches.
- pgvector, Qdrant, Pinecone, Chroma, and FAISS share `Vector Retrieval`. Their types retain
  important implementation differences. A consumer may select more than one with evidence.
- LangChain (`LLM Application Frameworks`), LangGraph (`Agent Orchestration`), and LlamaIndex
  (`Retrieval Frameworks`) have different focus areas and are not treated as exact substitutes.
- Link technologies to specific implementation capabilities where the connection is useful.
  For example, pgvector stores links to `rag` and `vector-search`, returning
  `Retrieval-Augmented Generation (RAG)` and `Vector search`. LangGraph returns `Agent workflows`
  and `Function calling`. Links describe possible uses, never candidate proficiency.
- Do not attach arbitrary capabilities to broad languages or tools merely to fill metadata.
  `[]` means no curated links, not that a technology cannot implement any capabilities.
- Capabilities and professional methods have no technology family. Source fields can default
  to `null` and `[]`; metadata fields are always included in `get_skills` responses.

The optional `selection_group` identifies a narrower architectural position than a technology
family. It is currently curated for 30 technologies in 9 groups, leaving the rest unset rather
than inferring hints from broad families. pgvector, Qdrant, Pinecone, and Chroma share
`Vector Storage`; FAISS uses `Vector Index`. PostgreSQL uses `Relational Storage`, so it remains
distinct from its vector extension. Other hints cover existing API frameworks, UI frameworks,
browser automation, cloud platforms, infrastructure provisioning, and analytical warehouses.
These are comparison/deduplication hints, never feature-equivalence claims, prerequisites, or
one-per-group rules. LangChain, LangGraph, and LlamaIndex have no forced selection group.
Preserve complementary technologies and multiple evidenced implementations when appropriate.
Only technologies can carry a group; omitted or null source values return `null`.

The optional `technology_ecosystems` list supplies curated language/runtime associations.
Reuse authored names: `Python`, `Java / JVM`, `JavaScript / TypeScript`, `Go`, `.NET`, `Rust`,
`PHP`, and `Ruby`. The full review also uses `Dart`, `Swift`, `Kotlin`, and `R`, and extends
associations across frontend, mobile, data, and AI technologies. The initial 28 associations
covered backend languages, frameworks, ORM libraries, package managers, and test tools,
including Python/FastAPI/Django/pytest,
Java/Spring Boot/JUnit, and JavaScript/TypeScript/Node.js/Express.js/NestJS.
Python and JavaScript versions of LangChain, LangGraph, and LlamaIndex carry both ecosystem
labels; Playwright carries its supported client-language ecosystems. Shared databases,
messaging, infrastructure, and capabilities need no language assignment.
Membership is nonexhaustive and does not describe the language a product was implemented in.
It is a selection hint, not a dependency graph, compatibility guarantee, or one-stack rule.
Support multiple labels when appropriate; do not reject evidenced work across ecosystems.
Omitted source lists default to `[]`, which is always returned by `get_skills` and means no
curated association. Only technologies may have nonempty lists. Startup rejects blank or
non-string names and duplicates after case/whitespace normalization. Ecosystems never add,
remove, reorder, or reprioritize options. The readable client displays nonempty associations.

Startup rejects duplicate canonical skill names after normalization, validates family
applicability and nonempty names, and rejects unknown, duplicate,
self-referencing, or mistyped capability references. Every link must target an existing skill of type
`implementation_capability`. References may point outside a response filtered by role,
seniority, or limit. Experience-only targets remain in source but are omitted from returned
capability links. Links do not add selections, alter counts/priorities, or override filters.
The five IDs noted in the review (`schema-validation`, `rest-apis`, `release-engineering`,
`sql-modeling`, and `distributed-tracing`) all exist in this full registry. They are deliberately
not forced into every role's returned subset. Selection groups also require nonempty names;
neither grouping deduplicates or changes eligible results. `get_roadmap` returns domain concepts
in its separate `industry_context` field.

Mappings are refined using existing IDs rather than adding generic synonyms. Redis now links to
`caching`, `authentication` (including session lifecycle), and `message-queues`; its description
identifies cache/session storage and acknowledged stream processing. FastAPI links to
`rest-apis`, `schema-validation`, and `openapi-contracts`. Pydantic, OpenTelemetry, LangGraph,
and Ragas retain their existing valid links. The `llm-evaluation` capability and Ragas descriptions
explicitly include retrieval and generation assessment, so a duplicate "RAG Evaluation" entry
is unnecessary. The catalog still contains 605 skills, and the AI profile returns 43 options.

The consuming resume LLM compares families, checks the JD and candidate evidence, and usually
selects approximately 15-25 skills as appropriate. It should demonstrate general practices in
experience bullets unless listing them is directly useful for the JD. Keep the discovery catalog
broad; do not impose a resume-sized source limit or discard alternatives without that context.

Primary references checked for the distinctions used in this refinement:

- [Node.js runtime](https://nodejs.org/en/about)
- [Apache Kafka event streaming](https://kafka.apache.org/)
- [RabbitMQ messaging broker](https://www.rabbitmq.com/)
- [GraphQL introduction](https://graphql.org/learn/introduction/)
- [pytest](https://docs.pytest.org/en/stable/), [JUnit](https://junit.org/),
  [Jest](https://jestjs.io/), [Vitest](https://vitest.dev/),
  and [XCTest](https://developer.apple.com/documentation/xctest)
- [GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions),
  [GitLab CI/CD](https://docs.gitlab.com/ci/), and [Jenkins](https://www.jenkins.io/)
- [FastAPI](https://fastapi.tiangolo.com/), [Django](https://www.djangoproject.com/),
  [Spring Boot](https://spring.io/projects/spring-boot/),
  [Express.js](https://expressjs.com/), and [NestJS](https://docs.nestjs.com/)
- [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview)
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LlamaIndex framework](https://developers.llamaindex.ai/python/framework/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [pgvector](https://github.com/pgvector/pgvector)
- [Redis streaming and consumer groups](https://redis.io/docs/latest/develop/use-cases/streaming/)
- [Ragas evaluation metrics](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/)

These references establish engineering scope; family labels, capability links, and priorities
are this catalog's editorial metadata, not a vendor classification or exhaustive dependency graph.

References checked for the five additions and canonical library names:

- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Pydantic](https://docs.pydantic.dev/latest/)
- [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview)
- [pgvector](https://github.com/pgvector/pgvector)
- [Ragas](https://docs.ragas.io/en/stable/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/index)

These sources establish product identity and scope. Role assignments and priorities are this
project's editorial choices. The consuming LLM matches the job description and verifies the
candidate's experience before selecting a compact final skills section.

## Sources and maintenance

The initial inventory came from the learning-roadmap references listed in the repository README.
This revision curates that existing inventory; it does not claim job-posting frequency or market
demand. Descriptions and role/seniority assignments are authored for this project.

Primary references checked for the revised protocol and instrumentation descriptions:

- [IETF HTTP semantics (RFC 9110)](https://www.rfc-editor.org/rfc/rfc9110.html)
- [OAuth 2.0 security guidance (RFC 9700)](https://www.rfc-editor.org/rfc/rfc9700.html)
- [PKCE (RFC 7636)](https://www.rfc-editor.org/rfc/rfc7636.html)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [PostgreSQL query plans](https://www.postgresql.org/docs/current/using-explain.html)
- [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/) and
  [context propagation](https://opentelemetry.io/docs/concepts/context-propagation/)
- [OWASP application logging guidance](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

Edit `skills/*.json`, `categories.json`, and the affected `roles/*.json` or `industries/*.json`
together. Include explicit skill types, technology families where applicable, curated capability
links, optional selection hints, and role-option priorities. Check role relevance,
category ownership, seniority, and duplication rather than
optimizing for a minimum catalog size. Keep concrete non-product skills in regression coverage
alongside literal technology names.

To validate only roadmap data, instantiate `Catalog(Path("data"))`; the CLI validation command
also loads the separate bullet catalog. The complete review excluded `data/bullets/`.

For full repository validation, run `uv run roadmap-mcp validate`, `uv run pytest`, `uv run ruff check .`, and
`uv run ruff format --check .` from the repository root. The server loads a snapshot at startup;
restart it to serve updated data.
