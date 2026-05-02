---
service: backend
summary: "JWKS client for Keycloak RS256 token validation"
paths: [backend/app/core/jwks.py]
flows: []
touches: []
external: [keycloak]
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Fetch and cache RS256 public keys from the Keycloak JWKS endpoint so
`core/auth.py` can validate production JWTs without embedding certificates.

## Interface
- `core/jwks.py::get_jwks()` → `dict | None` — return cached JWKS, refresh if stale
- `core/jwks.py::invalidate_jwks_cache()` → `None` — force refresh on next call
- `core/jwks.py::decode_keycloak_token(token)` → `dict | None` — verify RS256 signature and audience

## State
Thread-safe in-memory cache with TTL.

| symbol | type | semantics |
|---|---|---|
| `_jwks_cache` | `dict \| None` | Last fetched JWKS payload |
| `_cache_timestamp` | `float` | Monotonic timestamp of last successful fetch |
| `_cache_lock` | `threading.Lock` | Prevents thundering-herd on cache miss |
| `_CACHE_TTL_SECONDS` | `int` | 300 seconds |

Invariants:
- `_jwks_cache is not None ∧ (now - _cache_timestamp) < _CACHE_TTL_SECONDS` → `get_jwks()` returns cache without network call
- Fetch failure ⟂ stale cache available → returns stale cache; else returns None
- Thread safety: `_cache_lock` held during fetch and write; double-checked after acquire

## Internals
- Keycloak-disabled (`keycloak_enabled=false`) short-circuits to `None`
- `decode_keycloak_token` extracts `kid` from unverified header, looks up key in cached JWKS
- On `kid` miss: invalidates cache once, refetches, then retries lookup before giving up
- Issuer verification is relaxed (`verify_iss: False`) because Keycloak is reachable via multiple origins
- Audience is verified against `keycloak_client_id`
- All validation failures return `None`; the caller (`core/auth.py::authenticate_token`) falls through to the next strategy
- Network and JWT errors are logged but never raised to the auth path

## Touches
| resource | how | why |
|---|---|---|
| external/keycloak | HTTPS GET to JWKS endpoint (`/protocol/openid-connect/certs`) | Retrieve RS256 public keys |

## Gotchas
- `decode_keycloak_token` never raises; a `None` return can mean disabled Keycloak, unreachable endpoint, expired token, or bad signature
- Stale cache may be served indefinitely if the JWKS endpoint stays down; tokens signed with newly rotated keys will fail until the endpoint recovers
- Relaxed issuer check means tokens from any Keycloak realm on the same instance could pass signature validation if they share the same JWKS endpoint; audience check is the remaining boundary
