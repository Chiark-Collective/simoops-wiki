---
used_by: [backend, keycloak]
owner_team: infrastructure
---

# Data Stores

## PostGIS

| Parameter | Value |
|---|---|
| Image | postgis/postgis:15-3.3 |
| Port | 5432 |
| Data volume | `pgdata` (Docker volume) |
| Extensions | postgis, pg_trgm |

### Access

- Backend: SQLAlchemy async pool
- Keycloak: JDBC direct

### Quirks

- Password immutable after `pgdata` initialization
- See [gotchas.md](../gotchas.md)

## Redis

| Parameter | Value |
|---|---|
| Image | redis:7-alpine |
| Port | 6379 |
| Mode | Single instance (no cluster) |

### Access

- Backend: `redis.asyncio` for cache, pub/sub, presence

### Quirks

- No persistence configured; restart clears ephemeral state
- Fallback to in-memory buffer when unavailable

## Minio

| Parameter | Value |
|---|---|
| Image | minio/minio:latest |
| API port | 9000 |
| Console port | 9001 |
| Credentials | From env (`MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`) |

### Access

- Backend: `boto3` S3-compatible client
- Stores: floor plans, site maps, report exports, scene images

### Quirks

- Console requires separate port forwarding
- Bucket policies must allow public read for tile serving
