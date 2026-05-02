---
service: backend
summary: "Pydantic settings singleton loading SIMOOPS_* env vars"
paths: [backend/app/core/config.py]
flows: []
touches: [infra/data-stores]
external: [keycloak]
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Centralised application settings loaded from environment variables with the
`SIMOOPS_*` prefix. Provides a cached singleton so settings are parsed once
per process.

## Interface
- `core/config.py::Settings` — Pydantic `BaseSettings` class
- `core/config.py::Settings.model_config` — `env_prefix="SIMOOPS_"`, reads `.env`
- `core/config.py::Settings.assemble_cors_origins` — comma-split string validator
- `core/config.py::Settings.validate_keycloak_admin_secret` — production-gated validator
- `core/config.py::Settings.validate_redis_url` — rejects malformed Redis URLs at startup
- `core/config.py::Settings.keycloak_issuer_url` — public-facing OIDC issuer URL
- `core/config.py::Settings.keycloak_jwks_url` — internal JWKS endpoint URL
- `core/config.py::Settings.database_async_url` — `+psycopg_async://` variant
- `core/config.py::get_settings()` → `Settings` — `@lru_cache` singleton; auto-creates storage dirs

## State
Singleton `Settings` instance cached by `get_settings()`.

| symbol | type | semantics |
|---|---|---|
| `get_settings` | `lru_cache` wrapper | One `Settings` instance per process |

Invariants:
- First call to `get_settings()` creates `storage_dir` and `assets_dir` if missing
- `Settings` instance is immutable after creation

## Internals
- `test_jwt_secret_key` default `"change-me"` is safe because the HS256 path is gated to `environment == "test"`
- `keycloak_admin_client_secret` empty default forces explicit production opt-in rather than shipping a shared literal
- `keycloak_public_url` falls back to `keycloak_url` when unset for issuer validation
- `database_async_url` string-replaces `+psycopg://` with `+psycopg_async://`
- `run_migrations` is guarded by `SIMOOPS_RUN_MIGRATIONS=true`; uses PostgreSQL advisory lock with `migration_lock_timeout_seconds`
- `require_redis=true` causes `/health/ready` to return 503 when Redis is unconfigured; prevents silent divergence in multi-worker deploys

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | PostgreSQL URL, pool size, overflow, timeout | Database connections |
| infra/data-stores | `redis_url`, `require_redis` | Pub/sub and cache configuration |
| infra/data-stores | `minio_endpoint`, access keys, bucket | Object storage configuration |
| external/keycloak | `keycloak_url`, realm, client IDs | OIDC authentication configuration |

## Gotchas
- `keycloak_admin_client_secret` validation only runs when `keycloak_enabled=true` and `environment` is not development/docker/test; missing it in production raises `ValueError` at startup
- `redis_url` rejects non-redis:// schemes at validation time to surface misconfiguration early
- Changing `backend_cors_origins` env value after startup has no effect; the list is baked into the cached `Settings` instance
