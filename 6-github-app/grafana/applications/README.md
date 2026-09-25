# Applications

This folder contains 9 dashboard definitions for application monitoring, user analytics, and business metrics. Scenario 6 synchronizes them into **Git Sync GitHub App → Applications** in Grafana.

## Dashboards

Each link opens the dashboard's JSON definition.

| Dashboard | Contents |
| --- | --- |
| [API Performance](api-performance.json) | Response times, request and error rates, HTTP status codes, and total requests. |
| [Application Logs](application-logs.json) | Log volume by level and service, error and warning trends, and common error types. |
| [Database Metrics](database-metrics.json) | Query duration, database connections, transaction rates, slow queries, and cache hit rate. |
| [KPI Overview](kpi-overview.json) | Revenue and customer acquisition targets, monthly recurring revenue, customer satisfaction, and financial trends. |
| [Revenue Metrics](revenue-metrics.json) | Daily revenue and transactions, average order value, conversion rate, and revenue trends. |
| [Sales Pipeline](sales-pipeline.json) | Leads, qualified opportunities, win rate, pipeline value, funnel conversion, and closed deals. |
| [Service Health](service-health.json) | Service uptime, health checks, dependency status, overall health, and active incidents. |
| [User Engagement](user-engagement.json) | Daily and monthly active users, retention, new signups, user growth, and feature usage. |
| [Web Analytics](web-analytics.json) | Active users, page views, bounce rate, session duration, and top pages. |

## Supporting files

- [`_folder.json`](_folder.json) defines the **Applications** folder title and stable UID (`github-app-applications`). Keep `metadata.name` unchanged to preserve the folder's identity.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) contains dashboard contribution and verification guidance and serves as an example Markdown tab in Grafana.

## Navigation

[Dashboard catalog](../README.md) · [Infrastructure](../infrastructure/README.md) · [Scenario 6 setup guide](../../README.md)
