---
service: backend
summary: "JWKS client for Keycloak RS256 token validation with issuer verification and stale cache detection"
paths: [backend/app/core/jwks.py, backend/app/core/config.py]
flows: []
touches: []
external: [keycloak]
last_verified_commit: f9606469ce367229c5c91e03c3ba917779015030
---

## Purpose
Fetch and cache RS256 public keys from the Keycloak JWKS endpoint so
`core/auth.py` can validate production JWTs without embedding certificates.

## Interface
- `core/jwks.py::get_jwks()` → `dict | None` — return cached JWKS, refresh if stale
- `core/jwks.py::invalidate_jwks_cache()` → `None` — force refresh on next call
- `core/jwks.py::decode_keycloak_token(token)` → `dict | None` — verify RS256 signature, audience, and optionally issuer
- `core/jwks.py::get_jwks_cache_age_seconds()` → `float | None` — age since last successful fetch
- `core/jwks.py::is_jwks_serving_stale()` → `bool` — whether last `get_jwks()` fell back to stale cache

## State
Thread-safe in-memory cache with TTL and stale-circuit detection.

| symbol | type | semantics |
|---|---|---|
| `_jwks_cache` | `dict \| None` | Last fetched JWKS payload |
| `_cache_timestamp` | `float` | Monotonic timestamp of last successful fetch |
| `_cache_lock` | `threading.Lock` | Prevents thundering-herd on cache miss |
| `_CACHE_TTL_SECONDS` | `int` | 300 seconds |
| `_STALE_DEGRADED_THRESHOLD_SECONDS` | `int` | 600 seconds (2×TTL) |
| `_serving_stale` | `bool` | `True` when last call returned stale cache |

Invariants:
- `_jwks_cache is not None ∧ (now - _cache_timestamp) < _CACHE_TTL_SECONDS` → `get_jwks()` returns cache without network call
- Fetch failure ⟂ stale cache available → returns stale cache; else returns `None`
- `_serving_stale` flips `True` on first failed refresh after a successful one; flips `False` on first successful refresh after staleness — logged at WARN/INFO respectively
- Thread safety: `_cache_lock` held during fetch and write; double-checked after acquire

## Internals
- Keycloak-disabled (`keycloak_enabled=false`) short-circuits to `None`
- `decode_keycloak_token` extracts `kid` from unverified header, looks up key in cached JWKS
- On `kid` miss: invalidates cache once, refetches, then retries lookup before giving up
- Issuer verification gated by `keycloak_verify_issuer` (`SIMOOPS_KEYCLOAK_VERIFY_ISSUER`, default `False`); when `True`, verifies `iss` against `keycloak_issuer_url`
- Audience is verified against `keycloak_client_id`
- All validation failures return `None`; the caller (`core/auth.py::authenticate_token`) falls through to the next strategy
- Network and JWT errors are logged but never raised to the auth path
- `/health/ready` surfaces `jwks` component: `ok (age_s: N)` when fresh, `error: stale cache (age_s: N, serving_stale: True)` when degraded; probe flips to 503 when age > 2×TTL or `_serving_stale` is `True`

## Touches
| resource | how | why |
|---|---|---|
| external/keycloak | HTTPS GET to JWKS endpoint (`/protocol/openid-connect/certs`) | Retrieve RS256 public keys |

## Gotchas
- `decode_keycloak_token` never raises; a `None` return can mean disabled Keycloak, unreachable endpoint, expired token, or bad signature
