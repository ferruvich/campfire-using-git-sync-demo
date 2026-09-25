# Infrastructure

This folder contains 8 dashboard definitions for compute infrastructure, networking, cloud resources, and security. Scenario 6 synchronizes them into **Git Sync GitHub App → Infrastructure** in Grafana.

## Dashboards

Each link opens the dashboard's JSON definition.

| Dashboard | Contents |
| --- | --- |
| [Access Control & Authentication](access-control.json) | User sessions, authentication methods, permission changes, API key and token usage, and sessions by role. |
| [Cloud Resources](cloud-resources.json) | Cloud costs, VM instances, storage usage, service limits, and resources by region. |
| [Docker Containers](docker-containers.json) | Running and stopped containers, restarts, images, and container CPU and memory usage. |
| [Kubernetes Cluster](kubernetes-cluster.json) | Master and worker node status, running pods, namespaces, and node CPU and memory utilization. |
| [Load Balancers](load-balancers.json) | Request rates, connections, request distribution, backend health, and backend response times. |
| [Networking](networking.json) | Inbound and outbound bandwidth, regional latency, packet loss, and DNS query types. |
| [Security Overview](security-overview.json) | Failed logins, threat level, active incidents, suspicious activities, and security events by severity. |
| [Vulnerability Scan & Compliance](vulnerability-scan.json) | CVE counts and trends, compliance score, patch status, affected components, and scan results. |

## Supporting files

[`_folder.json`](_folder.json) defines the **Infrastructure** folder title and stable UID (`github-app-infrastructure`). Keep `metadata.name` unchanged to preserve the folder's identity.

## Navigation

[Dashboard catalog](../README.md) · [Applications](../applications/README.md) · [Scenario 6 setup guide](../../README.md)
