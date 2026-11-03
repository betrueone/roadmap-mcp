"""Run the MCP server or validate a catalog before deployment."""

import argparse
import json
import os
from pathlib import Path

from mcp.server.transport_security import TransportSecuritySettings

from roadmap_mcp.bullets import BulletCatalog
from roadmap_mcp.catalog import Catalog, CatalogError
from roadmap_mcp.server import create_server


def csv_env(name: str) -> list[str]:
    return [value.strip() for value in os.environ.get(name, "").split(",") if value.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Validate all data files and cross-references")
    serve = commands.add_parser("serve", help="Serve skill roadmaps and resume baselines over MCP")
    for command in (validate, serve):
        command.add_argument(
            "--data-dir", type=Path, default=Path(os.environ.get("ROADMAP_DATA_DIR", "data"))
        )
    serve.add_argument(
        "--transport", choices=["stdio", "streamable-http"], default="streamable-http"
    )
    serve.add_argument("--host", default=os.environ.get("ROADMAP_HOST", "127.0.0.1"))
    serve.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    serve.add_argument("--allowed-host", action="append", default=csv_env("ROADMAP_ALLOWED_HOSTS"))
    serve.add_argument(
        "--allowed-origin", action="append", default=csv_env("ROADMAP_ALLOWED_ORIGINS")
    )
    args = parser.parse_args()
    try:
        catalog = Catalog(args.data_dir)
        bullet_catalog = BulletCatalog(args.data_dir / "bullets")
    except CatalogError as error:
        parser.exit(1, f"Catalog validation failed: {error}\n")
    if args.command == "validate":
        print(
            json.dumps(
                {
                    "valid": True,
                    "roles": len(catalog.roles),
                    "industries": len(catalog.industries),
                    "seniority_levels": len(catalog.levels),
                    "skills": len(catalog.skills),
                    "categories": len(catalog.categories),
                    "bullet_catalog": {
                        "roles": len(bullet_catalog.roles),
                        "industries": len(bullet_catalog.industries),
                        "seniority_levels": len(bullet_catalog.levels),
                        "bullets": len(bullet_catalog.bullets),
                        "dataset_version": bullet_catalog.manifest.version,
                    },
                },
                indent=2,
            )
        )
        return
    server = create_server(catalog, bullet_catalog)
    if args.transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            stateless_http=True,
            json_response=True,
            transport_security=TransportSecuritySettings(
                enable_dns_rebinding_protection=True,
                allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*", *args.allowed_host],
                allowed_origins=[
                    "http://127.0.0.1:*",
                    "http://localhost:*",
                    "http://[::1]:*",
                    *args.allowed_origin,
                ],
            ),
        )


if __name__ == "__main__":
    main()
