---
used_by: [backend, ui, keycloak, minio, titiler]
owner_team: infrastructure
last_verified_commit: c56ee3d5
---

# Compute

## Netcup VPS 1000 G12

| Parameter | Value |
|---|---|
| vCores | 4 (AMD EPYC 9645) |
| RAM | 8 GB DDR5 ECC |
| Disk | 256 GB NVMe |
| Network | 2.5 Gbps |
| Location | Nuremberg, Germany |
| Cost | ~6 EUR/month |

## Access

- SSH alias: `simops` (used by `sync-from-prod.sh`)
- Repo path: `/opt/simops`
- No IaC — manual provisioning, no Terraform/Ansible

## Docker Compose

Orchestrator for all services. Two compose files:

| File | Mode | Key differences |
|---|---|---|
| `docker-compose.yml` | Development | Ports exposed to host; backend mounts source for hot reload; single uvicorn worker; Keycloak `start-dev` (H2, ephemeral); includes Mailpit |
| `docker-compose.prod.yml` | Production | Only Caddy exposes 80/443; `restart: unless-stopped`; gunicorn 4 workers; Keycloak `start` + dedicated PostgreSQL; JSON log rotation (10 MB / 3 files) |

### Production container resource limits

| Service | Image | mem_limit | Notes |
|---|---|---|---|
| caddy | Built from `ui/Dockerfile` | 256 MB | Caddy 2 + built Angular SPA |
| backend | Built from `backend/Dockerfile` | 3 GB | Gunicorn 4× uvicorn workers; `SIMOOPS_RUN_MIGRATIONS=true` |
| db | `postgis/postgis:16-3.4` | 2 GB | Volume `pgdata` |
| keycloak | `quay.io/keycloak/keycloak:latest` | 1500 MB | JVM heap capped 768 MB; dedicated `keycloak-db` |
| keycloak-db | `postgres:16-alpine` | 512 MB | Volume `keycloak-pgdata` |
| redis | `redis:7-alpine` | 256 MB | Volume `redis-data` |
| minio | `minio/minio:latest` | 512 MB | Volume `minio-data` |
| minio-setup | `minio/minio:latest` | — | One-shot bucket creator |
| **Total** | | **~9.5 GB** | **Exceeds 8 GB VPS RAM** |

## Quirks

- Total container memory ~9.84 GB exceeds 7.7 GB VPS; zero swap → repeated OOM kills. See [analysis](../analyses/oom-kill-cascade.md).
- Keycloak sessions lost on every restart (realm re-imported from `realm-export.json`)
- No zero-downtime deploy — `make prod-up` drops all WebSocket connections for ~10-30s
- `PROD_ENV_FILE` Makefile default is `.env` but docker-compose.prod.yml expects `.env.prod`
- No Minio backup in `backup.sh` — only PostgreSQL is backed up
- No offsite backup — `rclone copy` line in `backup.sh` is commented out

## Touches

| resource | how | why |
|---|---|---|
| [Network](network.md) | Docker bridge network | Inter-service communication |
| [Data Stores](data-stores.md) | Docker volumes | Persistent state |
