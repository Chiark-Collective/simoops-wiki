---
direction: both
consumed_by: [backend, ui]
auth: OIDC / Bearer JWT
---

# Keycloak

## Use

| Consumer | Use |
|---|---|
| backend | Token validation, userinfo, realm roles, site-scoped permissions |
| ui | Login redirect, token refresh, session management |

## Endpoints

| Endpoint | Purpose |
|---|---|
| `http://keycloak:8080/realms/{realm}/protocol/openid-connect/token` | Token exchange |
| `http://keycloak:8080/realms/{realm}/protocol/openid-connect/userinfo` | User info |
| `http://keycloak:8080/admin/realms/{realm}/users` | Admin user management |

## Failure handling

- Backend caches JWKS with TTL; fallback to local JWK on timeout
- Token expiry handled via 401 → ui refresh flow
- Keycloak restart without persistent volume loses realm config (mitigated by `keycloak-data` volume in docker-compose.yml)

## Quirks

- Requires ≥2 GB RAM (OOM at 1 GB)
- Redirect URIs now persist across restarts via `keycloak-data` volume (H2 database)
- Custom `simoops` branded login theme: CSS-only branding on `keycloak.v2` base, dark mode enabled, logo via CSS background-image
- Theme assets served through Caddy (`/resources/*`, `/js/*` routes proxy to Keycloak)
- `scripts/keycloak-set-login-theme.sh` patches theme on existing realm without re-import
- See [gotchas.md](../../gotchas.md)
