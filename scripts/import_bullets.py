"""Rebuild the runtime bullet datasource from the attached reference seed."""

import argparse
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from roadmap_mcp.bullet_models import BulletManifest, BulletRecord, BulletTaxonomy
from roadmap_mcp.bullets import BulletCatalog
from roadmap_mcp.catalog import Catalog, CatalogError, normalize, reject_duplicate_keys
from roadmap_mcp.models import NamedEntity

ROOT = Path(__file__).resolve().parents[1]

# Explicit aliases bridge the two catalogs without collapsing distinct reference roles.
ROLE_ALIASES = {
    "fullstack-engineer": "full-stack-engineer",
    "ai-llm-engineer": "ai-engineer",
    "security-engineer": "cybersecurity-engineer",
}
INDUSTRY_ALIASES = {
    "b2b-saas": "saas",
    "fintech-payments": "fintech",
    "banking-lending": "banking",
    "healthtech": "healthcare",
    "insurance-insurtech": "insurance",
    "ecommerce-retail": "e-commerce",
    "edtech": "education",
    "logistics-supplychain": "logistics",
    "gaming-entertainment": "gaming",
    "proptech": "real-estate",
    "manufacturing-iot": "manufacturing",
    "media-streaming": "media-entertainment",
    "government-public": "government",
    "energy-utilities": "energy",
}


def taxonomy_entries(
    reference_dir: Path,
    dimension: str,
    existing: dict[str, NamedEntity],
    mappings: dict[str, str],
    runtime_dir: Path,
) -> list[NamedEntity]:
    filename = "roles.json" if dimension == "role" else "industries.json"
    if not (reference_dir / filename).exists():
        taxonomy = BulletTaxonomy.model_validate(
            json.loads(
                (runtime_dir / "catalog.json").read_bytes(), object_pairs_hook=reject_duplicate_keys
            )
        )
        return taxonomy.roles if dimension == "role" else taxonomy.industries
    rows = json.loads(
        (reference_dir / filename).read_bytes(),
        object_pairs_hook=reject_duplicate_keys,
    )
    entries = []
    for row in rows:
        identifier, name = row[f"{dimension}_id"], row[dimension]
        aliases = set()
        previous = existing.get(mappings.get(identifier, identifier))
        if previous is not None:
            aliases.update([previous.id, previous.name, *previous.aliases])
        seen = {normalize(identifier), normalize(name)}
        accepted = []
        for alias in sorted(aliases, key=lambda value: (value.casefold(), value)):
            key = normalize(alias)
            if key not in seen:
                accepted.append(alias)
                seen.add(key)
        entries.append(NamedEntity(id=identifier, name=name, aliases=accepted))
    return entries


def import_bullets(reference_dir: Path, data_dir: Path) -> BulletCatalog:
    skills = Catalog(data_dir)
    destination = data_dir / "bullets"
    taxonomy = BulletTaxonomy(
        roles=taxonomy_entries(reference_dir, "role", skills.roles, ROLE_ALIASES, destination),
        industries=taxonomy_entries(
            reference_dir, "industry", skills.industries, INDUSTRY_ALIASES, destination
        ),
        seniority_levels=list(skills.levels.values()),
    )
    # Validate the entire import before replacing any runtime file.
    with TemporaryDirectory(prefix="roadmap-bullets-") as temporary:
        staging = Path(temporary)
        (staging / "catalog.json").write_text(
            taxonomy.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        _line_number = 0
        bullet_count = 0
        versions = set()
        try:
            with (
                (reference_dir / "bullets.jsonl").open(encoding="utf-8") as source,
                (staging / "bullets.jsonl").open("w", encoding="utf-8") as target,
            ):
                for _line_number, line in enumerate(source, 1):
                    if line.strip():
                        original = json.loads(line, object_pairs_hook=reject_duplicate_keys)
                        bullet = BulletRecord.model_validate(
                            {field: original[field] for field in BulletRecord.model_fields}
                        )
                        target.write(bullet.model_dump_json() + "\n")
                        bullet_count += 1
                        if "dataset_version" in original:
                            versions.add(original["dataset_version"])
        except (ValueError, KeyError) as error:
            raise CatalogError(f"Invalid bullets/bullets.jsonl:{_line_number}: {error}") from error
        if len(versions) > 1:
            raise CatalogError("Bullet seed contains conflicting dataset versions")
        manifest_path = reference_dir / "manifest.json"
        has_reference_manifest = manifest_path.exists()
        if not has_reference_manifest:
            manifest_path = destination / "manifest.json"
        original_manifest = json.loads(
            manifest_path.read_bytes(), object_pairs_hook=reject_duplicate_keys
        )
        if not has_reference_manifest:
            original_manifest.update(
                bullet_count=bullet_count,
                role_count=len(taxonomy.roles),
                industry_count=len(taxonomy.industries),
                seniority_levels=[level.id for level in taxonomy.seniority_levels],
                version=next(iter(versions), original_manifest["version"]),
            )
        manifest = BulletManifest.model_validate(
            {field: original_manifest[field] for field in BulletManifest.model_fields}
        )
        (staging / "manifest.json").write_text(
            manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        BulletCatalog(staging)
        destination.mkdir(parents=True, exist_ok=True)
        for file in sorted(staging.iterdir()):
            shutil.copyfile(file, destination / file.name)
        (destination / "sources.json").unlink(missing_ok=True)
    return BulletCatalog(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", type=Path, default=ROOT / "reference")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    try:
        catalog = import_bullets(args.reference_dir, args.data_dir)
    except (CatalogError, OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Bullet import failed: {error}\n")
    print(
        json.dumps(
            {
                "valid": True,
                "dataset_version": catalog.manifest.version,
                "bullets": len(catalog.bullets),
                "roles": len(catalog.roles),
                "industries": len(catalog.industries),
                "seniority_levels": len(catalog.levels),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
