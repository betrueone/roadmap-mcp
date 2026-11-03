#!/usr/bin/env bash
set -euo pipefail

if (( $# > 0 )); then
    if (( $# == 1 )) && [[ "$1" == "--help" || "$1" == "-h" ]]; then
        cat <<'HELP'
Usage: ./redeploy.sh

Build, validate, and redeploy the Roadmap MCP Docker Compose service.

ROADMAP_PORT          Override the published port. Otherwise use .env,
                      the existing service's port, or 8000, in that order.
ROADMAP_BIND_ADDRESS  Docker bind address (default: 127.0.0.1).
                      Set 0.0.0.0 in .env to accept remote IPv4 connections.
ROADMAP_WAIT_TIMEOUT  Seconds to wait for a healthy container (default: 120).
HELP
        exit 0
    fi
    printf 'Usage: ./redeploy.sh [--help]\n' >&2
    exit 2
fi

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_dir"

if ! command -v docker >/dev/null 2>&1; then
    printf 'Docker is required.\n' >&2
    exit 1
fi
docker compose version >/dev/null
docker info >/dev/null

compose=(docker compose --project-directory "$repo_dir" --file "$repo_dir/compose.yaml")
"${compose[@]}" config --quiet

redeploy_port="${ROADMAP_PORT:-}"
if [[ -z "$redeploy_port" ]]; then
    while IFS='=' read -r config_name config_value; do
        if [[ "$config_name" == "ROADMAP_PORT" ]]; then
            redeploy_port="$config_value"
        fi
    done < <("${compose[@]}" config --environment)
fi
if [[ -z "$redeploy_port" ]]; then
    published_address="$("${compose[@]}" port roadmap 8000 2>/dev/null || true)"
    redeploy_port="${published_address##*:}"
fi
redeploy_port="${redeploy_port:-8000}"
if [[ ! "$redeploy_port" =~ ^[1-9][0-9]{0,4}$ ]] || (( redeploy_port > 65535 )); then
    printf 'ROADMAP_PORT must be an integer from 1 to 65535.\n' >&2
    exit 2
fi
export ROADMAP_PORT="$redeploy_port"

wait_timeout="${ROADMAP_WAIT_TIMEOUT:-120}"
if [[ ! "$wait_timeout" =~ ^[1-9][0-9]*$ ]]; then
    printf 'ROADMAP_WAIT_TIMEOUT must be a positive integer.\n' >&2
    exit 2
fi

printf 'Building Roadmap MCP for port %s...\n' "$ROADMAP_PORT"
"${compose[@]}" build roadmap

printf 'Validating the mounted source data...\n'
"${compose[@]}" run --rm --no-deps -T roadmap validate

printf 'Recreating the service and waiting for health checks...\n'
if "${compose[@]}" up --detach --no-build --force-recreate --wait \
    --wait-timeout "$wait_timeout" roadmap; then
    "${compose[@]}" ps roadmap
    printf 'Roadmap MCP is ready: http://localhost:%s/mcp\n' "$ROADMAP_PORT"
else
    deploy_status=$?
    printf 'Redeploy failed. Current status and recent logs:\n' >&2
    "${compose[@]}" ps roadmap >&2 || true
    "${compose[@]}" logs --no-color --tail 80 roadmap >&2 || true
    exit "$deploy_status"
fi
