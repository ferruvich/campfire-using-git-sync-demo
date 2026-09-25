# Grafana Git Sync Demo Repository

> **Last Updated:** September 25, 2026
>
> **Purpose:** This repository provides practical demonstrations of Grafana's Git Sync feature through six real-world scenarios. It's designed to help DevOps engineers, SREs, and Grafana users learn how to implement bidirectional synchronization between Grafana dashboards and Git repositories.

## ⚠️ Important Disclaimers

- **Demo Configurations**: Scenarios 1–5 retain their original experimental Git Sync configuration from November 2025. These demos use moving container tags and default credentials; **we don't recommend using them in production or critical environments**.

- **Evolving Documentation**: Scenarios 1–5 retain their November 2025 setup instructions. Scenario 6 adds GitHub App authentication with mise and gcx. Please refer to the [official Grafana Git Sync documentation](https://grafana.com/docs/grafana/latest/as-code/observability-as-code/git-sync/) for the latest information.

## Overview

Demonstration of Grafana's Git Sync feature with six practical scenarios covering common deployment patterns.

## Scenarios

### Scenario 1: Default Setup

Single Grafana instance with Git Sync.

[→ Scenario 1 Guide](1-single/README.md)

### Scenario 2: Dev/Prod Environments

Two instances demonstrating dashboard promotion workflow.

[→ Scenario 2 Guide](2-dev-prod/README.md)

### Scenario 3: Multi-Region Deployment

Multiple instances syncing from the same shared directory.

[→ Scenario 3 Guide](3-multi-region/README.md)

### Scenario 4: Master-Replica with Load Balancer

High availability setup with master-replica instances and easy failover.

[→ Scenario 4 Guide](4-master-replica/README.md)

### Scenario 5: Multi-Team Setup

Single Grafana instance with multiple Git Sync repositories for different teams.

[→ Scenario 5 Guide](5-multi-team/README.md)

### Scenario 6: GitHub App with mise and gcx

Single Grafana instance with ngrok, GitHub App authentication, mise tasks, and your existing gcx installation, with 18 dashboards across applications, business, infrastructure, and security. Dashboard image previews are disabled.

[→ Scenario 6 Guide](6-github-app/README.md)

## Prerequisites

- Docker & Docker Compose
- Ngrok account with static subdomain ([ngrok.com](https://ngrok.com))
- GitHub account and a repository containing the scenario you want to sync
- **Scenarios 1–5:** GitHub Personal Access Token (scopes: repo, pull_requests, webhooks) and [grafanactl](https://grafana.github.io/grafanactl/)
- **Scenario 6:** [mise](https://mise.jdx.dev/getting-started.html), gcx installed on your PATH, the Docker Compose plugin, Bash, curl, envsubst, and a GitHub App installed on your repository. See the [scenario prerequisites](6-github-app/README.md#prerequisites).

## Quick Start

The Make and grafanactl commands below apply to **scenarios 1–5**. For scenario 6, follow the [GitHub App setup and mise quick start](6-github-app/README.md).

### 1. Fork this Repository

Click the "Fork" button on GitHub to create your own copy of this repository. You'll need to push changes to your fork for Git Sync to work.

### 2. Configure Environment

```bash
# At repository root
cp .env.example .env
```

Edit `.env` and configure:

- `NGROK_AUTHTOKEN`: Your ngrok auth token
- `NGROK_SUBDOMAIN`: Your static ngrok subdomain (e.g., `https://your-subdomain.ngrok-free.app`)
- `GITHUB_PAT`: Your GitHub Personal Access Token (scenarios 1–5)
- `GITHUB_REPO`: Your forked repository's full URL (e.g., `https://github.com/yourusername/campfire-using-git-sync-demo`)
- `GITHUB_BRANCH`: Branch to sync (usually `main`)

Scenario 6 also uses `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID`, and `GITHUB_APP_PRIVATE_KEY` (the base64-encoded PEM contents). Store these in the root, gitignored `.env`, which mise loads for its tasks. See [Configure the environment](6-github-app/README.md#configure-the-environment) for key preparation. Scenario 6 does not require `GITHUB_PAT`.

### 3. Choose and Start a Scenario

```bash
# Example: Start scenario 2
cd 2-dev-prod
make start
```

### 4. Configure Git Sync

After services start, run the setup script to configure Git Sync:

```bash
make setup-git-sync
```

This will:
- Wait for Grafana instances to be ready
- Create Repository resources via grafanactl
- Configure bidirectional sync with your GitHub fork

### 5. Verify Setup

```bash
# Get public URL
make ngrok-url

# Check Git Sync status
grafanactl --config=grafanactl.yaml resources get repositories
```

Access Grafana at `http://localhost:3000` (or the appropriate port) and login with `admin` / `admin`. Your dashboards should be synced from Git!

## Makefile Commands

Scenarios 1–5 include a Makefile with helpful commands:

```bash
make help          # Show all available commands
make start         # Start services
make open          # Open Grafana in browser
make ngrok-url     # Get public URL
make logs          # View logs
make health        # Check service health
make stop          # Stop services
make clean         # Remove all containers and volumes
```

Scenario 6 uses `mise run start`, followed by `mise run setup-resources` once Grafana is healthy. `setup-resources` renders the Connection and Repository templates with `envsubst` and pushes them with gcx. `mise run ngrok-url` prints the configured `NGROK_SUBDOMAIN`; `mise run setup-users` manages the demo editor and viewer accounts (requires Python 3). See its [task reference](6-github-app/README.md#tasks), including `mise run clean` for teardown.

## Git Sync Workflow

### Creating Dashboards

**In Grafana**:

1. Create dashboard
2. Save and choose: "Push to main" or "Create new branch"
3. Enter commit message
4. Click "Open Pull Request" if using branch workflow

**In Git**:

1. Create dashboard JSON in CRD format
2. Commit and push
3. Grafana syncs automatically (60s interval)

### Dashboard Format

```json
{
  "apiVersion": "dashboard.grafana.app/v1beta1",
  "kind": "Dashboard",
  "metadata": {
    "name": "dashboard-uid"
  },
  "spec": {
    // Dashboard configuration
  }
}
```

## Using grafanactl

Scenarios 1–5 include a `grafanactl.yaml` configuration file for CLI management. Scenario 6 uses gcx; see [Configure gcx contexts](6-github-app/README.md#configure-gcx-contexts) for the configuration used by each task and [Inspect Git Sync](6-github-app/README.md#inspect-git-sync) for commands. To use grafanactl:

### Installation

```bash
# Install grafanactl (see https://grafana.github.io/grafanactl/)
brew install grafanactl  # macOS
# or download from releases page
```

### Usage

```bash
# Navigate to scenario directory
cd 2-dev-prod

# List available contexts
grafanactl --config=grafanactl.yaml config get-contexts

# Switch context (scenario 2, 3, 4 only)
grafanactl --config=grafanactl.yaml config use-context prod

# List dashboards
grafanactl --config=grafanactl.yaml resources get dashboards

# Get specific dashboard
grafanactl --config=grafanactl.yaml resources get dashboard/<name>

```

### Context Names by Scenario

- **Scenario 1**: `default`
- **Scenario 2**: `dev`, `prod`
- **Scenario 3**: `us`, `eu`
- **Scenario 4**: `master`, `replica`
- **Scenario 5**: `default` (single instance with multiple repositories)

## Troubleshooting

The Make and grafanactl guidance here applies to scenarios 1–5. For scenario 6, use its [troubleshooting guide](6-github-app/README.md#troubleshooting).

### Ngrok Issues

```bash
make ngrok-url          # Get current URL
docker-compose logs ngrok
docker-compose restart ngrok
```

### Git Sync Not Working

1. Verify GitHub PAT has correct permissions (repo, pull requests, webhooks)
2. Check repository path matches directory structure
3. Review Grafana logs: `make logs`
4. Ensure ngrok URL is accessible

### Dashboards Not Appearing

1. Check Git Sync status: Administration → Provisioning
2. Wait 60s for sync interval
3. Force sync via UI: Pull button
4. Verify dashboard CRD format is correct

### Service Health

```bash
make health     # Check all services
make status     # Show container status
```

## Resources

- [Git Sync Documentation](https://grafana.com/docs/grafana/latest/as-code/observability-as-code/provision-resources/intro-git-sync/)
- [Git Sync Setup Guide](https://grafana.com/docs/grafana/latest/as-code/observability-as-code/provision-resources/git-sync-setup/)
- [Official Demo Repository](https://github.com/grafana/grafana-git-sync-demo)
