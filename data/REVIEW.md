# Complete roadmap datasource review

Follow-up correction on 2026-11-06: restored seven curated options previously filtered by role
category maps and technical projections for 14 industry capabilities. Every direct role/industry
assignment now has category coverage. Web Platform and Mobile Development are distinct response
categories; shared UI and backend runtime labels now match their scope. The source still has
605 skills in 43 categories, with 23 technical response categories. All 20 roles define explicit
`required_categories`, validated against their complete curated baseline. Added baseline options
cover backend observability, AI API integration and data governance, data-engineering security
and architecture, frontend architecture, ML authentication/privacy, and UX privacy. Existing skill
IDs and priorities are preserved. AI now has 43 options, Backend 47, Data Engineer 45, Frontend 40,
ML Engineer 42, and UX Designer 22. The review record below describes the earlier revision.

Reviewed on 2026-11-04. `data/bullets/`, the reference bullet dataset, and bullet behavior are excluded.

## Coverage and approach

All 605 skill definitions were read for names, types, descriptions, families, ecosystem hints, comparison groups, and capability links. All 20 role inventories and priority lists, all 300 role/industry mappings in 15 industry files, all 43 categories, and the four seniority levels were reviewed. The existing twelve type corrections from the backend pass were rechecked and retained. Changes below describe this additional, complete pass.

The inventory still contains 183 technologies, 370 implementation capabilities, 43 professional methods, and 9 soft skills. No skill IDs were added or removed. Catalog validation checks references, category ownership, metadata applicability, aliases, duplicate entries, priority bounds, and seniority ranks. Canonical skill-name uniqueness is now also enforced at startup.

Primary documentation was used to check disputed technology identities. Role priorities and entry thresholds are editorial recommendations, not vendor claims, market-frequency measurements, or universal job requirements. An entry threshold means a skill can be relevant at that level; it does not assert independent production ownership or candidate proficiency.

| Reviewed skill file | Entries |
| --- | ---: |
| [ai.json](skills/ai.json) | 13 |
| [analytics.json](skills/analytics.json) | 13 |
| [backend.json](skills/backend.json) | 24 |
| [cloud.json](skills/cloud.json) | 22 |
| [data.json](skills/data.json) | 25 |
| [design-product.json](skills/design-product.json) | 22 |
| [frontend.json](skills/frontend.json) | 18 |
| [industries.json](skills/industries.json) | 201 |
| [machine-learning.json](skills/machine-learning.json) | 16 |
| [management.json](skills/management.json) | 14 |
| [mobile.json](skills/mobile.json) | 14 |
| [quality.json](skills/quality.json) | 11 |
| [security.json](skills/security.json) | 11 |
| [shared.json](skills/shared.json) | 25 |
| [technologies.json](skills/technologies.json) | 176 |

## Technology classifications

27 additional classifications were corrected or made more specific:

| Stable ID | Technology | Previous type | Current type |
| --- | --- | --- | --- |
| `hls` | HTTP Live Streaming (HLS) | `standard` | `protocol` |
| `react` | React | `framework` | `library` |
| `cypress` | Cypress | `tool` | `test_framework` |
| `s3` | Amazon S3 | `infrastructure` | `cloud_service` |
| `azure-blob-storage` | Azure Blob Storage | `infrastructure` | `cloud_service` |
| `azure-data-factory` | Azure Data Factory | `tool` | `cloud_service` |
| `databricks-delta-lake` | Delta Lake | `database` | `framework` |
| `stripe-api` | Stripe API | `tool` | `api` |
| `shopify-storefront-api` | Shopify Storefront API | `tool` | `api` |
| `shopify-admin-api` | Shopify GraphQL Admin API | `tool` | `api` |
| `linux-cli` | Linux | `infrastructure` | `operating_system` |
| `rpc-contracts` | gRPC | `protocol` | `framework` |
| `aws` | AWS | `infrastructure` | `cloud_platform` |
| `azure` | Azure | `infrastructure` | `cloud_platform` |
| `google-cloud` | Google Cloud | `infrastructure` | `cloud_platform` |
| `ec2` | Amazon EC2 | `infrastructure` | `cloud_service` |
| `aws-lambda` | AWS Lambda | `infrastructure` | `cloud_service` |
| `aws-vpc` | Amazon VPC | `infrastructure` | `cloud_service` |
| `cloudfront` | Amazon CloudFront | `infrastructure` | `cloud_service` |
| `route53` | Amazon Route 53 | `infrastructure` | `cloud_service` |
| `aws-rds` | Amazon RDS | `infrastructure` | `cloud_service` |
| `aws-iam` | AWS IAM | `tool` | `cloud_service` |
| `opentelemetry` | OpenTelemetry | `tool` | `framework` |
| `core-data` | Core Data | `library` | `framework` |
| `combine` | Combine | `library` | `framework` |
| `firebase` | Firebase | `infrastructure` | `cloud_platform` |
| `locust` | Locust | `tool` | `test_framework` |

Identity references: [React](https://react.dev/) describes a UI library; [gRPC](https://grpc.io/) and [Delta Lake](https://delta.io/) describe frameworks. [OpenTelemetry](https://opentelemetry.io/docs/what-is-opentelemetry/) is an instrumentation framework/toolkit. Apple documents [Core Data](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CoreData/index.html) and [Combine](https://developer.apple.com/documentation/Combine?changes=_9) as frameworks. [HLS RFC 8216](https://www.rfc-editor.org/rfc/rfc8216.html) describes a streaming protocol.

The new `cloud_service` type distinguishes hosted services from installed tools: examples include [AWS IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html), [Amazon RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html), [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html), [Amazon EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html), [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html), and [Azure Data Factory](https://learn.microsoft.com/en-us/azure/data-factory/introduction). Cloud suites use `cloud_platform`; SQL/NoSQL engines and warehouses retain their more informative `database` identity, including managed products.

[Stripe](https://docs.stripe.com/api) and Shopify [Storefront](https://shopify.dev/docs/api/storefront/latest) / [Admin](https://shopify.dev/docs/api/admin-graphql/latest) entries identify APIs. The `api` type distinguishes these interfaces from client SDKs and implementation capabilities. [Cypress](https://docs.cypress.io/app/get-started/why-cypress) and [Locust](https://locust.io/) are categorized as test frameworks because their catalog entries describe authored executable tests and their execution systems.

Broad classifications were retained where useful: Docker, Kubernetes, Nginx, Hadoop YARN, and HDFS remain infrastructure with specific families. Playwright and Selenium remain automation tools: the generic entries include automation APIs, not only a bundled test runner. Ragas remains an evaluation tool. This review does not force every tool into a new single-product type.

## Names, descriptions, categories, and relationships

19 technology display names were made explicit or normalized to their project names. IDs remain stable:

| Stable ID | Previous name | Current name |
| --- | --- | --- |
| `s3` | S3 | Amazon S3 |
| `azure-data-factory` | Data Factory (ETL) | Azure Data Factory |
| `databricks-delta-lake` | Databricks Delta Lake | Delta Lake |
| `pandas` | Pandas | pandas |
| `tls-cryptography` | SSL/TLS | TLS |
| `ec2` | EC2 | Amazon EC2 |
| `aws-lambda` | Lambda | AWS Lambda |
| `aws-vpc` | VPC | Amazon VPC |
| `cloudfront` | CloudFront | Amazon CloudFront |
| `aws-rds` | RDS | Amazon RDS |
| `aws-iam` | IAM | AWS IAM |
| `nmap` | NMAP | Nmap |
| `tcpdump` | Tcpdump | tcpdump |
| `gitlab-ci` | GitLab CI | GitLab CI/CD |
| `argocd` | ArgoCD | Argo CD |
| `fastlane` | Fastlane | fastlane |
| `room` | Room Database | Room |
| `kotlin-coroutines` | Coroutines | Kotlin Coroutines |
| `scikit-learn` | Scikit-learn | scikit-learn |

Naming references include [Argo CD](https://argo-cd.readthedocs.io/en/stable/), [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-overview.html), [Room](https://developer.android.com/training/data-storage/room), [pandas](https://pandas.pydata.org/), [scikit-learn](https://scikit-learn.org/stable/), and [TLS](https://www.rfc-editor.org/rfc/rfc8446.html).

- Renamed the capability `healthcare-data` from Healthcare data concepts to Healthcare record modeling, matching its existing applied description.
- Made JavaScript and TypeScript descriptions useful for browser and server roles. Git now describes Git operations instead of hosting-service pull requests. The Kotlin Coroutines description names `kotlinx.coroutines`.
- Moved Azure SQL Database to Databases & Caching alongside relational databases.
- Moved component libraries and design tokens to User Experience & Design, and made component-library wording apply to web and native UI. Mobile roles no longer acquire a web-framework category solely through a shared design-system skill.
- Corrected React-family and comparison-group wording to include libraries, gRPC to RPC Frameworks, and Room/Core Data to the shared Mobile Persistence family.
- Linked Shopify Storefront API to cart state rather than inventory consistency ownership; retained inventory consistency for the Admin API. Linked Helm to workload operations and deployment rollbacks rather than claiming reproducible build/artifact promotion from Helm alone.
- Extended curated ecosystem hints from 28 to 73 technologies, including frontend, mobile, data, and AI stacks. Multi-language tools can have several labels; no automatic exclusion or single-stack rule was added. [Playwright](https://playwright.dev/) lists TypeScript, Python, Java, and .NET APIs; [LangGraph TypeScript](https://docs.langchain.com/oss/javascript/langgraph/overview) and [LlamaIndex.TS](https://developers.llamaindex.ai/typescript/framework/) support the additional JavaScript/TypeScript associations.

All 422 nontechnology definitions were reviewed. Reusable statistical, design, product, and management methods retain `professional_method`; scoped engineering and industry workflows retain `implementation_capability`; interpersonal behaviors remain `soft_skill`. Applied security, quality, and governance deliverables can remain implementation capabilities even when demonstrated through tests, runbooks, or review artifacts rather than code.

## Role priorities and seniority

64 existing role priorities were revised. Alternative language stacks, cloud vendors, frameworks, provider integrations, and work-tracking products generally use P2 in generic roles. Core work stays P1. The full-stack profile now prioritizes HTML/CSS and schema modeling; Product Manager prioritizes roadmapping and prioritization; SRE prioritizes operational automation. Python can remain P1 in Python-centered AI/ML/data profiles, and Swift in iOS: this is not a blanket demotion of every language or tool.

50 existing role thresholds were changed from Mid-level to Junior for basic framework use, testing tools, schema/authentication work, SDK integration, or baseline model validation. Complex orchestration, synchronization, architecture, and specialist industry modeling retain later thresholds. The seniority IDs, order, aliases, and cumulative selection mechanism were reviewed and retained.

PHP and Ruby were already in the registry but only added by e-commerce context. They are now P3 alternatives in both backend and full-stack role catalogs at Junior and above. Backend has 46 options (31 technologies / 15 capabilities), and Full Stack has 43. Other role option counts are unchanged. AI retains 41 options and its four P1 capabilities.

Every role was reviewed; this table records each resulting change:

| Role | Options | Priority changes | Newly junior-eligible existing skills |
| --- | ---: | --- | --- |
| AI Engineer | 41 | OpenAI SDK P1→P2; Pydantic P1→P2; FastAPI P1→P2; pgvector P1→P2; Docker P1→P2 | FastAPI, OpenAI SDK, Pydantic, pytest |
| Android Developer | 36 | Java P1→P2 | Jetpack Compose, JUnit |
| Backend Engineer | 46 | PostgreSQL P1→P2; Redis P1→P2; Docker P1→P2 | TypeScript, Django, Flask, FastAPI, Spring Boot, Express.js, NestJS, pytest, JUnit, Jest |
| Cloud Engineer | 40 | Python P1→P2; AWS P1→P2; Azure P1→P2; Google Cloud P1→P2; Terraform P1→P2 | Retained |
| Cybersecurity Engineer | 37 | Python P1→P2; Bash P1→P2; Wireshark P1→P2; Nmap P1→P2; tcpdump P1→P2 | Retained |
| Data Analyst | 31 | Excel P1→P2; Python P1→P2; pandas P1→P2; Git P1→P2 | Retained |
| Data Engineer | 42 | PostgreSQL P1→P2; Apache Airflow P1→P2; dbt P1→P2; Apache Spark P1→P2 | Retained |
| Data Scientist | 39 | R P1→P2 | scikit-learn, Feature engineering, Classification and regression pipelines, Leakage-safe model validation, Unit testing, Integration testing |
| DevOps Engineer | 41 | Python P1→P2; GitHub Actions P1→P2 | Retained |
| Engineering Manager | 19 | Jira P1→P2 | Retained |
| Frontend Engineer | 39 | React P1→P2; npm P1→P2; Vite P1→P2 | TypeScript, React, Vue.js, Angular, Svelte, Vite, Jest, Vitest, Client-side routing |
| Full Stack Engineer | 43 | Node.js P1→P2; React P1→P2; PostgreSQL P1→P2; HTML P2→P1; CSS P2→P1; Relational schema design P2→P1 | TypeScript, React, Vue.js, Express.js, NestJS, Python, FastAPI, Session and token authentication, Role-based and resource-level authorization, Relational schema design, Schema validation |
| iOS Developer | 32 | Retained | XCTest |
| Machine Learning Engineer | 40 | PyTorch P1→P2 | Retained |
| Mobile Engineer | 33 | JavaScript P1→P2; TypeScript P1→P2; Dart P1→P2; React Native P1→P2; Flutter P1→P2 | Retained |
| Platform Engineer | 39 | Python P1→P2; Go P1→P2; GitHub Actions P1→P2 | Retained |
| Product Manager | 24 | Jira P1→P2; Linear P1→P2; Product prioritization P2→P1; Product roadmapping P2→P1 | Retained |
| QA Engineer | 35 | Python P1→P2; JavaScript P1→P2; TypeScript P1→P2; SQL P1→P2; Postman P1→P2; Playwright P1→P2; pytest P1→P2 | Python, JavaScript, TypeScript, pytest, Playwright, Cypress, Selenium |
| Site Reliability Engineer | 38 | Python P1→P2; Go P1→P2; Operational runbook automation P2→P1 | Retained |
| UX Designer | 21 | Figma P1→P2 | Retained |

## Industry review

All 15 industry files and all 300 supported role/industry combinations were reviewed. Industry additions remain contextual P3 options and never promote a role baseline.

- Removed the e-commerce-only PHP/Ruby additions after making them general backend/full-stack alternatives.
- Removed the server/payment-record-oriented Stripe API entry from frontend and native mobile Fintech mappings. Those profiles retain payment UX, authentication, and event/workflow skills. Backend, full-stack, and data integration mappings retain the API. This is a scope decision for the existing entry, not a claim that UI engineers cannot integrate Stripe; [Stripe documents distinct client and server API-key use](https://docs.stripe.com/keys).
- Made 12 domain access-boundary skills available to Mid-level QA alongside their corresponding workflow tests. Financial reconciliation remains at its existing QA threshold, and complex operational/security architecture thresholds remain unchanged.
- Reviewed shared domain modeling, privacy, protocol/standard references, role specializations, and overlap precedence. Healthcare mappings needed no further changes. No industry or role coverage was removed.

| Industry | Role coverage | Result |
| --- | ---: | --- |
| Banking | 20 | QA access-boundary checks available at Mid-level |
| E-commerce | 20 | Moved language alternatives into generic roles |
| Education | 20 | QA access-boundary checks available at Mid-level |
| Energy and Utilities | 20 | QA access-boundary checks available at Mid-level |
| Fintech | 20 | Kept server API integration out of UI-only defaults |
| Gaming | 20 | QA access-boundary checks available at Mid-level |
| Government and Public Sector | 20 | QA access-boundary checks available at Mid-level |
| Healthcare | 20 | Reviewed; mappings retained |
| Insurance | 20 | QA access-boundary checks available at Mid-level |
| Logistics and Supply Chain | 20 | QA access-boundary checks available at Mid-level |
| Manufacturing | 20 | QA access-boundary checks available at Mid-level |
| Media and Entertainment | 20 | QA access-boundary checks available at Mid-level |
| Real Estate | 20 | QA access-boundary checks available at Mid-level |
| SaaS | 20 | QA access-boundary checks available at Mid-level |
| Telecommunications | 20 | QA access-boundary checks available at Mid-level |

## Validation and compatibility

- Roadmap-only catalog validation passes for 605 skills, 20 roles, 15 industries, 43 categories, and four levels.
- 200 non-bullet tests pass, including coverage across 1,200 role/industry/seniority combinations, canonical-name resolution, cumulative selection, metadata propagation, priorities, limits, and MCP skill responses.
- Ruff lint and formatting checks pass. The excluded bullet data has no diff.
- `get_skills` exposes four additional type values in this pass: `api`, `operating_system`, `cloud_platform`, and `cloud_service`. Clients with copied enums must accept these. Stable skill IDs remain the identity contract; clients relying on display names will observe the naming corrections.
- `get_roadmap` keeps its response shape, but names, categories, and some junior selections change with the corrected data. The server loads a snapshot, so restart it to serve these changes.

## Limits retained deliberately

JD matching, candidate verification, final resume selection, and `jd_priority` remain downstream responsibilities. Ecosystem lists are hints, not a dependency graph or exhaustive compatibility matrix. Industry-specific results can contain more than 50 eligible options; the current response limit and available/returned counts still apply. No popularity or labor-market claims were inferred from this review.
