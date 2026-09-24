#!/usr/bin/env bash

set -euo pipefail

SCENARIO_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
REPO_ROOT=$(cd -- "$SCENARIO_DIR/.." && pwd)
cd -- "$SCENARIO_DIR"

fail() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

for tool in gcx envsubst curl; do
    command -v "$tool" >/dev/null 2>&1 || fail "$tool is required; see the scenario README."
done

[[ -f "$REPO_ROOT/.env" ]] || fail "Create the repository-root .env from .env.example and configure it first."
source "$REPO_ROOT/.env"

for variable in GITHUB_REPO GITHUB_BRANCH GITHUB_APP_ID GITHUB_APP_INSTALLATION_ID GITHUB_APP_PRIVATE_KEY_FILE; do
    [[ -n "${!variable:-}" ]] || fail "$variable must be set in the repository-root .env."
done

[[ "$GITHUB_APP_ID" =~ ^[0-9]+$ ]] || fail "GITHUB_APP_ID must be the numeric App ID, not the Client ID."
[[ "$GITHUB_APP_INSTALLATION_ID" =~ ^[0-9]+$ ]] || fail "GITHUB_APP_INSTALLATION_ID must be numeric."
[[ "$GITHUB_REPO" =~ ^https://github\.com/[^/[:space:]]+/[^/[:space:]]+/?$ ]] || fail "GITHUB_REPO must be a full https://github.com/owner/repository URL."
[[ "$GITHUB_BRANCH" != *$'\n'* && "$GITHUB_BRANCH" != *$'\r'* ]] || fail "GITHUB_BRANCH must be a single line."
[[ "$GITHUB_APP_PRIVATE_KEY_FILE" = /* ]] || fail "GITHUB_APP_PRIVATE_KEY_FILE must be an absolute path to the PEM file."
[[ -f "$GITHUB_APP_PRIVATE_KEY_FILE" && -r "$GITHUB_APP_PRIVATE_KEY_FILE" && -s "$GITHUB_APP_PRIVATE_KEY_FILE" ]] || fail "The GitHub App PEM file must exist, be readable, and be nonempty."

echo "Waiting up to 60 seconds for Grafana at http://localhost:3000..."
deadline=$((SECONDS + 60))
ready=false
while (( SECONDS < deadline )); do
    timeout=$((deadline - SECONDS))
    if (( timeout <= 0 )); then
        break
    fi
    if (( timeout > 2 )); then
        timeout=2
    fi
    if response=$(curl --fail --silent --show-error --connect-timeout "$timeout" --max-time "$timeout" http://localhost:3000/api/health 2>/dev/null) &&
        printf '%s\n' "$response" | grep -E '"database"[[:space:]]*:[[:space:]]*"ok"' >/dev/null; then
        ready=true
        break
    fi
    if (( SECONDS < deadline )); then
        sleep 1
    fi
done
[[ "$ready" = true ]] || fail "Grafana did not become healthy within 60 seconds. Start it with 'mise run start' and check 'mise run logs-grafana'."

umask 077
TEMP_DIR=
cleanup() {
    if [[ -n "$TEMP_DIR" ]]; then
        rm -rf -- "$TEMP_DIR"
    fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
TEMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/git-sync-github-app.XXXXXX")
mkdir -- "$TEMP_DIR/connection" "$TEMP_DIR/repository"

# Escape single quotes for the quoted YAML scalars in repository.yaml.
GITHUB_REPO_YAML=$(printf '%s' "$GITHUB_REPO" | sed "s/'/''/g")
GITHUB_BRANCH_YAML=$(printf '%s' "$GITHUB_BRANCH" | sed "s/'/''/g")
export GITHUB_REPO_YAML GITHUB_BRANCH_YAML GITHUB_APP_ID GITHUB_APP_INSTALLATION_ID

# The template indents the first line; indent the remaining PEM lines to match.
# Normalizing CRLF also accepts keys downloaded on Windows.
GITHUB_APP_PRIVATE_KEY=$(tr -d '\r' < "$GITHUB_APP_PRIVATE_KEY_FILE" | sed '2,$s/^/      /')
export GITHUB_APP_PRIVATE_KEY
envsubst '${GITHUB_APP_ID} ${GITHUB_APP_INSTALLATION_ID} ${GITHUB_APP_PRIVATE_KEY}' \
    < connection.yaml > "$TEMP_DIR/connection/connection.yaml"
unset GITHUB_APP_PRIVATE_KEY
envsubst '${GITHUB_REPO_YAML} ${GITHUB_BRANCH_YAML}' \
    < repository.yaml > "$TEMP_DIR/repository/repository.yaml"

echo "Provisioning GitHub App connection..."
gcx --config="$SCENARIO_DIR/gcx.yaml" --context=default resources push \
    --path "$TEMP_DIR/connection" --on-error abort

echo "Provisioning Git Sync repository..."
gcx --config="$SCENARIO_DIR/gcx.yaml" --context=default resources push \
    --path "$TEMP_DIR/repository" --on-error abort

echo "Git Sync resources configured. Grafana will sync from 6-github-app/grafana/."
echo "Check Administration → Provisioning → Git Sync for connection and sync status."
