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

# Individual assignments split broad source categories and industry-specific capabilities.
_SKILL_GROUPS = {
    "Programming Languages": (
        "python java go csharp php ruby rust javascript typescript bash kotlin swift dart r "
        "sql advanced-sql"
    ),
    "Data Warehouses & Lakehouses": (
        "snowflake google-bigquery amazon-redshift databricks-delta-lake "
        "data-warehousing lakehouse-storage"
    ),
    "Data Modeling & Transformation": (
        "dbt sql-modeling nosql-modeling data-transformations schema-evolution "
        "ledger-modeling metric-modeling financial-data healthcare-data commerce-domain "
        "saas-domain education-domain banking-domain insurance-domain telecom-domain "
        "media-domain gaming-domain logistics-domain manufacturing-domain energy-domain "
        "real-estate-domain government-domain"
    ),
    "Workflow Orchestration": "apache-airflow workflow-scheduling workmanager",
    "Streaming & Change Data Capture": (
        "apache-kafka stream-processing change-data-capture payment-event-modeling "
        "order-event-processing learning-event-pipelines "
        "product-event-pipelines banking-event-pipelines insurance-event-pipelines "
        "playback-event-pipelines game-event-pipelines shipment-event-pipelines "
        "industrial-event-pipelines energy-event-pipelines property-event-pipelines"
    ),
    "Data Quality & Governance": (
        "data-quality data-lineage data-catalogs data-contracts data-access-governance "
        "data-retention data-platform-governance clinical-terminology clinical-data-validation "
        "healthcare-deidentification healthcare-provenance material-traceability "
        "financial-reconciliation"
    ),
    "Data Processing & ETL/ELT": (
        "financial-reporting-data fraud-feature-pipelines "
        "healthcare-data-ingestion customer-identity-resolution call-detail-processing "
        "public-data-pipelines"
    ),
    "CI/CD & DevOps": "mobile-release android-studio xcode",
    "APIs & Service Integration": (
        "retrofit okhttp mobile-networking real-time-apis payment-idempotency "
        "payment-lifecycle settlement-processing payment-disputes "
        "inventory-consistency pricing-promotions order-orchestration returns-refunds "
        "catalog-search subscription-lifecycle assessment-workflows banking-posting "
        "loan-servicing underwriting-workflows claims-workflows telecom-provisioning "
        "usage-charging media-transcoding matchmaking-services player-economy "
        "shipment-tracking warehouse-allocation metering-workflows property-search "
        "lease-workflows public-case-management public-record-publication"
    ),
    "Third-Party Integrations": (
        "webhook-integrations stripe-api three-d-secure payment-gateway-integration "
        "payment-webhooks fhir-integration smart-on-fhir shopify-storefront-api "
        "shopify-admin-api fulfillment-integration lti learning-platform-integration "
        "iso20022 tmforum-api hls opc-ua production-integration energy-asset-integration "
        "reso-web-api dcat firebase push-notifications native-integration"
    ),
    "Databases & ORMs": "room core-data mobile-persistence",
    "Distributed Systems & Messaging": "offline-synchronization",
    "Architecture & System Design": (
        "healthcare-interoperability-architecture saas-service-isolation assessment-capacity "
        "data-serving hilt"
    ),
    "Observability & Reliability": (
        "data-recovery mobile-crash-diagnostics mobile-performance payment-workload-reliability "
        "healthcare-service-reliability commerce-peak-reliability banking-recovery "
        "insurance-service-reliability telecom-observability stream-delivery-operations "
        "game-session-reliability tracking-service-reliability industrial-edge-reliability "
        "energy-service-reliability listing-service-reliability public-service-reliability"
    ),
    "Security & Authentication": (
        "payment-data-protection payment-authentication patient-identity consent-enforcement "
        "healthcare-access-controls entitlement-management tenant-isolation "
        "student-data-protection "
        "banking-authorization claims-access-controls subscriber-identity-controls media-rights "
        "media-entitlements game-abuse-controls shipment-access-controls ot-security "
        "energy-system-security property-data-access public-information-controls fraud-signals"
    ),
    "Testing & Quality Engineering": (
        "payment-scenario-testing healthcare-workflow-testing checkout-scenario-testing "
        "saas-workflow-testing assessment-testing banking-invariant-testing coverage-rule-testing "
        "telecom-provisioning-testing playback-testing multiplayer-testing "
        "shipment-workflow-testing "
        "production-workflow-testing metering-validation-testing property-workflow-testing "
        "public-eligibility-testing eslint prettier"
    ),
    "BI & Analytics": (
        "fintech-product-analytics healthcare-analytics commerce-analytics commerce-metrics "
        "subscription-metrics saas-usage-analytics learning-analytics credit-portfolio-analytics "
        "insurance-loss-analytics telecom-service-analytics audience-analytics "
        "game-engagement-analytics logistics-analytics production-analytics energy-analytics "
        "property-market-analytics public-service-analytics commerce-event-tracking"
    ),
    "AI/ML & LLM Engineering": (
        "financial-risk-modeling financial-document-extraction "
        "clinical-outcome-modeling clinical-document-retrieval commerce-recommendation "
        "commerce-document-extraction saas-churn-modeling saas-knowledge-retrieval "
        "learner-outcome-modeling education-knowledge-retrieval credit-risk-modeling "
        "banking-knowledge-retrieval insurance-risk-modeling insurance-knowledge-retrieval "
        "network-anomaly-modeling telecom-knowledge-retrieval content-recommendation "
        "media-metadata-extraction match-quality-modeling game-content-retrieval "
        "route-optimization "
        "logistics-document-extraction predictive-maintenance maintenance-knowledge-retrieval "
        "energy-demand-forecasting energy-document-retrieval property-valuation "
        "property-document-extraction public-demand-modeling public-guidance-retrieval"
    ),
    "Frontend & UI Engineering": (
        "design-systems design-tokens "
        "payment-ux financial-ui-formatting accessible-healthcare-ux clinical-workflow-ui "
        "patient-portal-usability cart-state product-discovery-ui commerce-seo saas-account-ui "
        "subscription-interface learner-interfaces banking-interfaces policyholder-interfaces "
        "subscriber-interfaces media-player-interfaces player-interfaces dispatch-interfaces "
        "operator-interfaces energy-interfaces property-interfaces citizen-interfaces"
    ),
    "User Experience & Design": "financial-disclosure-design",
}
_SKILL_CATEGORIES = {
    skill_id: category
    for category, skill_ids in _SKILL_GROUPS.items()
    for skill_id in skill_ids.split()
}


def response_category(skill_id: str, source_category: str) -> str:
    """Map technical skills to the response taxonomy, retaining nontechnical categories."""
    return _SKILL_CATEGORIES.get(skill_id, _SOURCE_CATEGORIES.get(source_category, source_category))
