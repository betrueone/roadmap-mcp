# Role × Industry Resume Bullet Baselines — v1.0.0

Data-only seed for a resume-content retrieval system. **No MCP server implementation included.**

## Coverage
- **17 engineering/technical roles × 20 industries × 6 baselines = 2,040 original example bullets.**
- 6 bullets per pair: 1 junior, 2 mid, 2 senior, 1 staff.
- Each baseline has role/industry IDs, topic/focus, O*NET broad occupation reference, NAICS broad industry reference, suggested evidence to verify, and verification status.

## Files
- `bullets.jsonl` — one JSON object per line; best for ingestion and search indexing.
- `bullets.json` — full JSON array of all bullets.
- `bullets.csv` — flat export for QA / manual review.
- `baseline_bullets.sqlite` — relational database with `roles`, `industries`, `bullets`, and (when supported) FTS5 `bullet_search`.
- `roles.json`, `industries.json`, `sources.json`, `manifest.json` — taxonomy, provenance and coverage metadata.

## Important data-quality rules
1. These are **original editorial examples**, not copied resumes and not claims about any real worker.
2. They are **occupation-informed and industry-contextualized**, not individually validated against primary role-specific industry job postings.
3. `is_candidate_fact=false`, `requires_personal_verification=true` and `verification_status=unverified_example` for every row.
4. No numerical impacts or performance metrics were fabricated. Any resume use requires evidence-based tailoring to the individual's actual work.
5. Some O*NET codes are **broad proxy occupation mappings**, not unique classifications of the specialized job title.
6. The industry taxonomy is editorial and its NAICS codes are high-level references, not formal unique subindustry mappings.
7. Terms like HIPAA, PCI, regulatory compliance are *not* automatically asserted as universal obligations; applicability depends on employer/system.

## Example SQLite query
```sql
SELECT seniority, focus, bullet
FROM bullets
WHERE role_id = 'backend-engineer' AND industry_id = 'fintech-payments'
ORDER BY CASE seniority WHEN 'junior' THEN 1 WHEN 'mid' THEN 2 WHEN 'senior' THEN 3 ELSE 4 END, focus;
```

## Primary references
- O*NET 31.0 database: https://www.onetcenter.org/database.html
- O*NET content license: https://www.onetcenter.org/license_db.html
- BLS OOH software developers and QA: https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm
- NAICS 2022: https://www.census.gov/programs-surveys/economic-census/year/2022/guidance/understanding-naics.html
- ESCO: https://esco.ec.europa.eu/en/use-esco/download
- Canada NOC / OaSIS: https://www.canada.ca/en/employment-social-development/services/noc.html

## Recommended additional ingestion
For the next iteration, download O*NET 31.0 Task Statements, Task Ratings, Software Skills and Occupation Data as separate licensed datasets, preserve each original task ID and license attribution, and add a human-reviewed layer of specialized engineering job descriptions by vertical. Do not label the editorial bullets as verbatim O*NET tasks or as facts drawn from real candidates.
