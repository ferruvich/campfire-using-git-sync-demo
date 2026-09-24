#!/usr/bin/env bash

set -euo pipefail

SCENARIO_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd -- "$SCENARIO_DIR"

cleanup_failed=false
# Delete the referencing repository before deleting its connection.
for resource in repositories/git-sync-github-app connections/github-app; do
    printf 'Removing %s...\n' "$resource"
    if ! gcx --config="$SCENARIO_DIR/gcx.yaml" --context=localhost resources delete "$resource" --yes --on-error abort; then
        printf 'Could not remove %s; it may already be absent or Grafana may be stopped. See the error above.\n' "$resource" >&2
        cleanup_failed=true
    fi
done

echo "Stopping services and removing this scenario's containers and volumes..."
docker compose --env-file ../.env down -v
if [[ "$cleanup_failed" = true ]]; then
    echo "Docker teardown complete; Git Sync resource cleanup could not be fully confirmed." >&2
else
    echo "Git Sync resources and Docker services cleaned up."
fi
