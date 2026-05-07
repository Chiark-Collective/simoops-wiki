---
used_by: [backend, ui, keycloak, minio, titiler]
owner_team: infrastructure
---

# Network

## Docker Compose Network

All services share a default bridge network (`simoops_default`).

| Service | Internal hostname | Exposed port |
|---|---|---|
| backend | `backend` | 8000 |
| ui | `ui` | 4200 |
| keycloak | `keycloak` | 8080 |
| postgis | `postgis` | 5432 |
| redis | `redis` | 6379 |
| minio | `minio` | 9000, 9001 |
| titiler | `titiler` | 8088 |

## Caddy Reverse Proxy

| External route | Upstream |
|---|---|
| `/api/*` | backend:8000 |
| `/ws` | backend:8000 (WebSocket upgrade) |
| `/` | ui:4200 (static SPA) |
| `/auth/*` | keycloak:8080 |
| `/resources/*` | keycloak:8080 | Keycloak theme CSS/fonts (was falling through to SPA catch-all) |
| `/js/*` | keycloak:8080 | Keycloak JS (`keycloak.js`) (was falling through to SPA catch-all) |
| `/tiles/*` | titiler:8088 |
| `/minio/*` | minio:9001 (console) |

## TLS

- Local: self-signed via Caddy internal CA
- Production: Let's Encrypt or custom cert mounted into Caddy

## Quirks

- Caddy handles WebSocket upgrade transparently
- Internal service-to-service calls use Docker DNS hostnames
- Port 8000 backend is never exposed directly; always via Caddy

## See also

- [Topology](../topology.md)
- [Gotchas](../gotchas.md)
