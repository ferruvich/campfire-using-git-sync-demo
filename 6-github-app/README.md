# Scenario 6: GitHub App with mise and gcx

Single Grafana instance with Git Sync authenticated through a GitHub App. This scenario runs Grafana and ngrok with the same 22 dashboards as [Scenario 1](../1-single/README.md), using mise tasks and your existing gcx installation.

## Architecture

```mermaid
graph LR
    User[User] --> Grafana[Grafana Instance]
    Grafana <--> |Git Sync via GitHub App| GitHub[GitHub Repository]
    Ngrok[ngrok Tunnel] --> Grafana

    style Grafana fill:#f96332
    style GitHub fill:#333
```

The GitHub App credentials are stored in a Grafana `Connection` named `github-app`. The `Repository` named `git-sync-github-app` references that connection and synchronizes `6-github-app/grafana/`. Grafana manages installation tokens using the app's private key; no GitHub Personal Access Token is required for this scenario.

## Prerequisites

- Docker with the Docker Compose plugin (`docker compose`).
- [mise-en-place](https://mise.jdx.dev/getting-started.html), Bash, curl, and `envsubst` (provided by GNU gettext) on your PATH.
- [gcx](https://github.com/grafana/gcx) installed and available on your PATH.
- Python 3 for the optional `setup-users` task (standard library only).
- An ngrok account with a static domain and auth token.
- A GitHub repository containing this scenario on the branch you intend to sync.
- A GitHub App installed on that repository, with its App ID, installation ID, and downloaded private key.

mise runs the tasks using the tools already on your PATH. No tool installation through mise is needed. The included `gcx.yaml` uses the context-based [configuration supported by gcx 0.2.15](https://github.com/grafana/gcx/blob/v0.2.15/docs/reference/configuration/index.md).

Run one scenario at a time: this scenario retains Grafana port **3000** from Scenario 1.

## Create and install the GitHub App

If you already have an app, check its permissions and repository installation against these steps. See [Grafana's GitHub App prerequisites](https://grafana.com/docs/grafana/latest/as-code/observability-as-code/git-sync/git-sync-setup/set-up-before/#create-a-github-app) for the upstream instructions.

1. Open [GitHub App registration](https://github.com/settings/apps/new), or your organization's **Settings → Developer settings → GitHub Apps**.
2. Choose a unique app name and set the homepage URL to your public ngrok URL. In the **Webhook** section, clear **Active**; Grafana configures repository webhooks for Git Sync.
3. Under **Repository permissions**, configure:

   | Permission | Access |
   | --- | --- |
   | Administration | Read-only |
   | Contents | Read and write |
   | Metadata | Read-only |
   | Pull requests | Read and write |
   | Webhooks | Read and write |

4. Select **Only on this account** for installation availability, then create the app.
5. Copy the numeric **App ID** (not the Client ID). Generate a private key and store the downloaded PEM file **outside this repository**.
6. Select **Install App**, choose your account, and grant access to the repository used for this demo.
7. Copy the numeric **installation ID** from the installation page URL, such as `https://github.com/settings/installations/12345678`.

## Configure the environment

Use the shared repository-root `.env`. If you do not already have one, copy `.env.example` to `.env` from the repository root. If it already exists, add the app variables without replacing your existing settings.

```dotenv
NGROK_AUTHTOKEN=your_ngrok_authtoken
NGROK_SUBDOMAIN=https://your-domain.ngrok-free.app
GITHUB_REPO=https://github.com/your_username/campfire-using-git-sync-demo
GITHUB_BRANCH=main
GITHUB_APP_ID=123456
GITHUB_APP_INSTALLATION_ID=12345678
GITHUB_APP_PRIVATE_KEY_FILE="/absolute/path/outside/the/repository/github-app.pem"
```

`GITHUB_APP_PRIVATE_KEY_FILE` must be an absolute path to a readable PEM file; quote it if the path contains spaces. Keep the PEM contents in that file. `GITHUB_PAT` may remain configured for other scenarios, but this scenario does not use it.

The configured remote branch must already contain `6-github-app/grafana/`. Commit and push the new scenario to your fork, or select a branch where it is already present, before configuring Git Sync.

## Quick start

From the repository root:

```bash
cd 6-github-app
mise trust

mise run start
mise run setup-git-sync
mise run ngrok-url
mise run open
```

Login at `http://localhost:3000` with `admin` / `admin`.

`start` starts the containers. `setup-git-sync` separately loads the shared `.env`, validates the required app inputs, and waits up to 60 seconds for Grafana health. It renders `connection.yaml` and `repository.yaml` into private temporary files and pushes the Connection before the Repository with gcx. Temporary files are removed when setup exits, including after an error or interrupt.

If you previously started this scenario with the image renderer, run `mise run start` to apply the updated services and remove the old renderer container. Run `mise run setup-git-sync` again to apply the disabled dashboard preview setting to an existing Git Sync repository.

The YAML files are templates: use the setup task to supply the credentials and repository settings. The script uses the local `gcx.yaml` and `default` context explicitly. It does not need an interactive gcx login or a context switch.

## Admin account and email

The initial admin email is **daniele.ferru@grafana.com**, configured through `GF_SECURITY_ADMIN_EMAIL` in `docker-compose.yml`. Grafana's [admin email setting](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/#admin_email) applies when the initial admin account is created.

`gcx.yaml` holds the credentials used to connect as `admin`; its [configuration schema](https://github.com/grafana/gcx/blob/v0.2.15/docs/reference/configuration/index.md) has no email field or user-provisioning settings. The email is noted there in a comment for reference. Grafana authenticates the supplied credentials and enforces the account's permissions on the server. Setting `user: admin` in a client file does not grant admin privileges.

The email is an initial value, not a continuously enforced policy. With an existing `grafana-data` volume, changing the Compose setting or restarting Grafana does not update the account. Sign in as `admin`, open **Profile**, edit the email, and save it; see [Edit your profile](https://grafana.com/docs/grafana/latest/administration/user-management/user-preferences/#edit-your-profile). Additional users have their own profiles; this setting only applies to the initial admin.

## Create additional users with mise

`users.json` defines the accounts managed by `mise run setup-users`:

| Username | Display name | Email | Organization 1 role | Password environment variable |
| --- | --- | --- | --- | --- |
| `editor` | Editor | `editor@example.com` | Editor | `GRAFANA_EDITOR_PASSWORD` |
| `viewer` | Viewer | `viewer@example.com` | Viewer | `GRAFANA_VIEWER_PASSWORD` |

Edit that file to change the demo emails or add users. JSON lets the helper use Python's standard library without an additional YAML parser. Each entry contains `login`, `name`, `email`, `role`, and `password_env`; passwords belong in the root, gitignored `.env` or exported environment variables.

Add your chosen passwords to the root `.env` before creating the accounts. Use shell quoting for spaces and special characters:

```dotenv
GRAFANA_EDITOR_PASSWORD='replace-with-your-editor-password'
GRAFANA_VIEWER_PASSWORD='replace-with-your-viewer-password'
```

Then, from this scenario directory:

```bash
mise run start
mise run setup-users
```

The task loads the root `.env` when present, then uses `gcx api` with the local `gcx.yaml` and `default` context. It requires the configured account's actual Grafana server administrator privileges and basic authentication. New users are created through the [Admin API](https://grafana.com/docs/grafana/latest/developer-resources/api-reference/http-api/api-legacy/admin/#global-users); profiles and membership are managed through the [User API](https://grafana.com/docs/grafana/latest/developer-resources/api-reference/http-api/api-legacy/user/) and [Organization API](https://grafana.com/docs/grafana/latest/developer-resources/api-reference/http-api/api-legacy/org/).

Each run matches existing usernames, updates their names and emails, and applies the requested role in organization 1. Passwords are required only for new accounts; existing passwords are never reset. `Admin` means organization Admin. The task refuses to manage server administrators or the account authenticating the requests, and it never deletes users. Removing an entry from the file leaves that account in Grafana.

Definitions, email conflicts, and required creation passwords are checked before any writes. Passwords are passed to gcx through standard input, without temporary credential files. API errors stop the task with a nonzero exit status; successful earlier changes remain, and rerunning finishes the setup. If Grafana is still starting, retry after it is healthy. These settings are applied when the task runs; there is no continuous user synchronization. `setup-users` is separate from `start` and `setup-git-sync`.

## Tasks

Every task corresponding to Scenario 1's Make targets is available through `mise run`:

| Command | Purpose |
| --- | --- |
| `mise run help` | List tasks |
| `mise run start` | Start services |
| `mise run setup-git-sync` | Create or update the app connection and Git Sync repository |
| `mise run setup-users` | Create or update the users and organization roles in `users.json` |
| `mise run stop` | Stop services, retaining their data volume |
| `mise run restart` | Restart services |
| `mise run logs` | Follow all service logs |
| `mise run logs-grafana` | Follow Grafana logs |
| `mise run logs-ngrok` | Show ngrok logs |
| `mise run ngrok-url` | Show the public tunnel URL |
| `mise run open` | Open Grafana |
| `mise run open-ngrok` | Open the ngrok dashboard |
| `mise run open-all` | Open both dashboards |
| `mise run health` | Check Grafana health and ngrok startup logs |
| `mise run status` | Show service status |
| `mise run clean` | Remove this scenario's Git Sync resources, containers, and volumes |

`clean` requests deletion of `repositories/git-sync-github-app` followed by `connections/github-app`, then runs Docker Compose teardown with volume removal. Cleanup errors remain visible, and Docker teardown still runs if Grafana is already stopped or the resources are absent. This does not uninstall the GitHub App or remove its private key file.

## Inspect Git Sync

From this scenario directory:

```bash
gcx --config=gcx.yaml --context=default config list-contexts
gcx --config=gcx.yaml --context=default resources get connections/github-app
gcx --config=gcx.yaml --context=default resources get repositories/git-sync-github-app
gcx --config=gcx.yaml --context=default resources get dashboards
```

In Grafana, open **Administration → Provisioning → Git Sync** to inspect connection and synchronization status. Dashboards are imported from `6-github-app/grafana/` into a folder named **Git Sync GitHub App**, with a 60-second sync interval.

Each dashboard folder (`applications`, `business`, `infrastructure`, `monitoring`, and `security`) includes a [`_folder.json` manifest](https://grafana.com/docs/grafana-cloud/learn-and-build/as-code/observability-as-code/git-sync/use-git-sync/#the-git-sync-folder-metadata-file). Its `metadata.name` stores a stable folder UID, and `spec.title` supplies the display name in Grafana. Keep the UID unchanged when moving or renaming a folder; move its manifest along with its dashboards.

The included UIDs are for a new setup. If these folders have already been synced without metadata, set each manifest's `metadata.name` to that folder's existing UID from its Grafana URL before syncing these files. This preserves the existing folder identity and permissions. Commit and push the manifests to the configured branch so Git Sync can read them.

Once configured, you can edit dashboards in Grafana or Git, write directly to the configured branch, or use the branch and pull request workflow. Dashboard image previews on pull requests are disabled because this scenario does not run an image renderer.

## Troubleshooting

- **mise shell configuration warning:** The scenario uses `[settings].unix_default_inline_shell_args`, which is supported by mise 2026.3.9. That version does not support `[task_config].shell`.
- **gcx not found:** Ensure the directory containing your installed gcx executable is on your PATH before running mise. This scenario does not declare a gcx tool dependency or download it from GitHub.
- **User setup errors:** Ensure Python 3 is installed, Grafana is ready, and `gcx.yaml` contains working server administrator credentials. Set the password variables named in `users.json` for accounts that do not yet exist. Reruns preserve existing passwords.
- **Missing app inputs:** Add the three `GITHUB_APP_*` variables to the root `.env`. Use the numeric App ID and installation ID, and a readable absolute PEM path.
- **Connection or repository errors:** Check that the app is installed on the selected repository with the permissions listed above. Inspect the resources with gcx and read `mise run logs-grafana`.
- **Grafana health timeout:** Check `mise run status` and `mise run logs-grafana`, then retry setup once Grafana is healthy.
- **No dashboards:** Confirm that the selected remote branch contains `6-github-app/grafana/`, and inspect Git Sync status. Local unpushed files are not synchronized.
- **Ngrok:** Check `mise run logs-ngrok` and `mise run ngrok-url`. The public URL in `NGROK_SUBDOMAIN` must match your static ngrok domain.
- **Ports already in use:** Stop the other scenario before starting this one.

## References

- [Set up Git Sync as code](https://grafana.com/docs/grafana/latest/as-code/observability-as-code/git-sync/git-sync-setup/set-up-code/)
- [gcx 0.2.15 configuration reference](https://github.com/grafana/gcx/blob/v0.2.15/docs/reference/configuration/index.md)
- [mise task configuration](https://mise.jdx.dev/tasks/task-configuration.html)
