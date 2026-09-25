# Contributing

This is an example Markdown file demonstrating the ability to view tabs in Grafana.

## Before you start

Follow the [Scenario 6 setup guide](README.md) to connect Grafana to your GitHub repository. Git Sync watches `6-github-app/grafana/` on the branch configured by `GITHUB_BRANCH` and checks for changes every 60 seconds.

Dashboards belong in [Applications](grafana/applications/) or [Infrastructure](grafana/infrastructure/), under **Git Sync GitHub App** in Grafana. Paths below are relative to `6-github-app/`.

## Add, update, or delete dashboards in Git

1. Create a working branch from the configured sync branch.
2. Make your dashboard change:

   | Action | What to change |
   | --- | --- |
   | Add | Copy an existing dashboard JSON into `grafana/applications/` or `grafana/infrastructure/` with a new filename. Give it a unique `metadata.name` (dashboard UID), update `spec.title`, and adapt its panels and queries. Preserve the copied resource's API version and structure. |
   | Update | Edit the existing dashboard JSON. Keep `metadata.name` unchanged so the dashboard retains its identity. |
   | Delete | Remove the dashboard's JSON file. Once the deletion reaches the configured branch and syncs, Grafana removes that dashboard. |

3. Keep the destination folder's `_folder.json` manifest unchanged. Update the [dashboard catalog](grafana/README.md) when adding, deleting, or renaming a dashboard, and adjust dashboard counts in that catalog, the [scenario README](README.md), and the [root README](../README.md) when needed.
4. Review the diff before committing.
5. Commit and push your changes, then open a pull request targeting the configured sync branch. Review and merge it. Direct commits to that branch also work when repository permissions allow them.

## Add or update dashboards in Grafana

1. Open the provisioned **Applications** or **Infrastructure** folder under **Git Sync GitHub App**.
2. To add a dashboard, choose **New dashboard** and configure its panels. To update one, open it and select **Edit**.
3. Select **Save dashboard**, confirm the destination folder and filename, and enter a descriptive commit message.
4. Save to a new branch and use **Open a pull request** to review and merge into the configured sync branch. You can also save directly to that branch when allowed. Keep the dashboard catalog and counts current through Git as described above.

Use the Git deletion workflow above to remove a dashboard. See [Grafana's Git Sync dashboard guide](https://grafana.com/docs/grafana/latest/as-code/observability-as-code/git-sync/provisioned-dashboards/) for more details.

## Verify the result

After your change reaches the configured sync branch, allow a sync cycle and refresh Grafana. Confirm that the dashboard appears, reflects your edits, or has been removed. Local edits and unmerged branches do not update the shared synced dashboards.

If the change does not appear, check **Administration → Provisioning → Git Sync** for synchronization status and errors, and confirm that you pushed to the repository and branch configured for this scenario.
