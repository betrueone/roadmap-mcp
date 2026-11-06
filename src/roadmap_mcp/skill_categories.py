"""Resume response taxonomy; source and compatibility-roadmap categories stay intact."""

TECHNICAL_CATEGORIES = (
    "Programming Languages",
    "Web Platform",
    "Frontend & UI Engineering",
    "Backend Frameworks & Runtimes",
    "Mobile Development",
    "APIs & Service Integration",
    "Databases & ORMs",
    "Data Warehouses & Lakehouses",
    "Data Modeling & Transformation",
    "Data Processing & ETL/ELT",
    "Workflow Orchestration",
    "Streaming & Change Data Capture",
    "Data Quality & Governance",
    "BI & Analytics",
    "Distributed Systems & Messaging",
    "Cloud & Infrastructure",
    "CI/CD & DevOps",
    "Observability & Reliability",
    "Security & Authentication",
    "Testing & Quality Engineering",
    "Architecture & System Design",
    "Third-Party Integrations",
    "AI/ML & LLM Engineering",
)

NONTECHNICAL_ROLE_CATEGORIES = {
    "data-analyst": ("Product Management",),
    "qa-engineer": ("Engineering Management",),
    "ux-designer": ("User Experience & Design", "Product Management"),
    "product-manager": (
        "Product Management",
        "User Experience & Design",
        "Engineering Management",
    ),
    "engineering-manager": ("Engineering Management", "Product Management"),
}

_SOURCE_CATEGORIES = {
    "Frontend Frameworks & UI": "Frontend & UI Engineering",
    "APIs & Integration": "APIs & Service Integration",
    "Databases & Caching": "Databases & ORMs",
    "Data Engineering & Analytics": "Data Processing & ETL/ELT",
    "Messaging & Streaming": "Distributed Systems & Messaging",
    "Cloud Infrastructure & Storage": "Cloud & Infrastructure",
    "Containers & Deployment": "CI/CD & DevOps",
    "Developer Tools & Code Quality": "CI/CD & DevOps",
    "Testing": "Testing & Quality Engineering",
    "Security & Privacy": "Security & Authentication",
    "System Design & Architecture": "Architecture & System Design",
    "Analytics & Statistics": "BI & Analytics",
    "Machine Learning": "AI/ML & LLM Engineering",
    "AI Engineering": "AI/ML & LLM Engineering",
    "Model Integration & Validation": "AI/ML & LLM Engineering",
    "LLM Frameworks & Orchestration": "AI/ML & LLM Engineering",
    "Vector Retrieval": "AI/ML & LLM Engineering",
    "LLM Evaluation Tools": "AI/ML & LLM Engineering",
}

# Individual assignments split broad source categories for resume skills.
_SKILL_GROUPS = {
    "Programming Languages": (
        "python java go csharp php ruby rust javascript typescript bash kotlin swift dart r sql "
        "advanced-sql"
    ),
    "Data Warehouses & Lakehouses": (
        "snowflake google-bigquery amazon-redshift databricks-delta-lake data-warehousing "
        "lakehouse-storage"
    ),
    "Data Modeling & Transformation": (
        "dbt sql-modeling nosql-modeling data-transformations schema-evolution metric-modeling"
    ),
    "Workflow Orchestration": "apache-airflow workflow-scheduling workmanager",
    "Streaming & Change Data Capture": "apache-kafka stream-processing change-data-capture",
    "Data Quality & Governance": (
        "data-quality data-lineage data-catalogs data-contracts data-access-governance "
        "data-retention data-platform-governance"
    ),
    "CI/CD & DevOps": "mobile-release android-studio xcode",
    "APIs & Service Integration": "retrofit okhttp mobile-networking real-time-apis",
    "Third-Party Integrations": (
        "webhook-integrations stripe-api three-d-secure fhir-integration smart-on-fhir "
        "shopify-storefront-api shopify-admin-api lti iso20022 tmforum-api hls opc-ua "
        "reso-web-api dcat firebase push-notifications native-integration"
    ),
    "Databases & ORMs": "room core-data mobile-persistence",
    "Distributed Systems & Messaging": "offline-synchronization",
    "Architecture & System Design": "data-serving hilt",
    "Observability & Reliability": "data-recovery mobile-crash-diagnostics mobile-performance",
    "Testing & Quality Engineering": "eslint prettier",
    "Frontend & UI Engineering": "design-systems design-tokens",
}
_SKILL_CATEGORIES = {
    skill_id: category
    for category, skill_ids in _SKILL_GROUPS.items()
    for skill_id in skill_ids.split()
}


def response_category(skill_id: str, source_category: str) -> str:
    """Map technical skills to the response taxonomy, retaining nontechnical categories."""
    return _SKILL_CATEGORIES.get(skill_id, _SOURCE_CATEGORIES.get(source_category, source_category))
