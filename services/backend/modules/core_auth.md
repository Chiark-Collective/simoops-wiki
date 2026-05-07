---
service: backend
summary: "JWT authentication, JWKS validation, and user resolution"
paths: [backend/app/core/auth.py, backend/app/core/jwks.py, backend/app/core/security.py]
flows: []
touches: [infra/data-stores]
external: [keycloak]
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose
Authenticate incoming requests via Keycloak RS256 JWTs or test-only HS256
tokens, resolve the token to a User record, and auto-create or link users on
first login.

## Interface
- `core/auth.py::authenticate_token(token, session)` → User
  Entry point shared by HTTP (`api/deps.py::get_current_user`) and WebSocket auth.
- `core/auth.py::_resolve_keycloak_user(payload, session)` → User
  Look up by `keycloak_sub`; fall back to email-based linking; auto-create on miss.
- `core/auth.py::_resolve_test_token(token, session)` → User
  HS256 decode gated to `environment == "test"`.
- `core/auth.py::_accept_pending_invites(session, email, user_id)` → None
  Best-effort invite acceptance on login; failures logged, never block auth.
  After creating new memberships, calls `ws_manager.invalidate_user_context(user_id, site_id)` for each newly created site to refresh cached permissions.
- `core/jwks.py::decode_keycloak_token(token)` → dict | None
  Attempt RS256 decode via cached JWKS; returns None on any failure so caller can fall back.
- `core/jwks.py::get_jwks()` → dict | None
  Return cached JWKS, refreshing if stale; thread-safe via lock.
- `core/jwks.py::invalidate_jwks_cache()` → None
  Force refresh on next call; used after key rotation.
- `core/security.py::create_test_access_token(subject, expires_minutes)` → str
  Mint HS256 JWT gated to `environment == "test"`.

## State
JWKS key cache maintained by `core/jwks.py`.

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
- Production path: RS256 via Keycloak JWKS; `keycloak_enabled` setting gates the entire path
- `decode_keycloak_token` does NOT raise on validation failure — returns None so `authenticate_token` can try next strategy
- Issuer verification is relaxed (`verify_iss: False`) because the same Keycloak instance is reachable via multiple origins
- On `kid` miss: cache invalidated once and refetched before giving up
- Test fallback: HS256 with `test_jwt_secret_key`, available only when `settings.environment == "test"`
- `_resolve_keycloak_user` tries three resolution strategies in order: `keycloak_sub` exact match → email case-insensitive link → auto-create
- Email linking updates `User.keycloak_sub` and commits immediately; subsequent logins match via `keycloak_sub`
- Auto-created users have no SiteMemberships; site access requires invite or admin action

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | SQLModel select/insert on `User` | Resolve or create user record |
| external/keycloak | HTTPS GET JWKS endpoint | Fetch RS256 public keys |

## Gotchas
- Contractor tokens (`sub` prefix `"contractor:"`) are rejected with 401 in both Keycloak and test paths
- `_resolve_test_token` asserts `environment == "test"`; calling it in production is a programming error
- `create_test_access_token` also asserts `environment == "test"`; minting in prod produces unusable tokens
- JWKS fetch failures are silently swallowed; auth falls through to test path (in test) or returns 401
