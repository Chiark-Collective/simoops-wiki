---
---

# Topology

| Service | Runtime | Listens | Upstream | Downstream |
|---|---|---|---|---|
| backend | Docker (FastAPI) | 8000 | PostGIS, Redis, Keycloak, Minio, TiTiler | ui (HTTP + WebSocket) |
| ui | Docker (nginx) | 4200 | backend (API + static assets) | — |
| keycloak | Docker | 8080 | PostGIS (user store) | backend, ui |
| postgis | Docker | 5432 | — | backend, keycloak |
| redis | Docker | 6379 | — | backend |
| minio | Docker | 9000 / 9001 | — | backend |
| titiler | Docker | 8088 | — | backend |

## Port Matrix

Canonical ports from `ports.env`:

| Service | Port |
|---|---|
| backend | 8000 |
| ui | 4200 |
| keycloak | 8080 |
| postgis | 5432 |
| redis | 6379 |
| minio-api | 9000 |
| minio-console | 9001 |
| titiler | 8088 |

## Data Flow

- ui → backend: HTTP (API calls), WebSocket (real-time events)
- backend → postgis: SQL (persistent data)
- backend → redis: cache, pub/sub, presence
- backend → minio: S3-compatible object storage (images, exports)
- backend → titiler: tile rendering requests
- backend ↔ keycloak: OIDC token validation, user info
- keycloak → postgis: user/role persistence
