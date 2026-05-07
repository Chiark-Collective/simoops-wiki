---
producer: ui
consumers: [backend, keycloak]
schema: frontend/src/app/core/auth/auth.service.ts
breaking_changes: []
---

## Purpose
Defines the OIDC authentication flow between Angular frontend, FastAPI backend, and Keycloak.

## Schema
`frontend/src/app/core/auth/auth.service.ts`

## Consumers
| service | uses | flow |
| backend | Bearer token, JWT claims | REST + WebSocket auth |
| keycloak | OIDC /authorize, /token, /logout | Authorization Code + PKCE |

## Flow

### Login
1. `LoginComponent` → `AuthService.login()` → `OidcSecurityService.authorize()`
2. Keycloak redirect → user authenticates → redirect to `/` with `code`
3. `angular-auth-oidc-client` exchanges `code` for Access Token (RS256 JWT), ID Token, Refresh Token
4. `AuthGuard` → `AuthService.checkAuthOnInit()` → `OidcSecurityService.checkAuth()`
5. Token stored in-memory (`_token`)
6. `UserService.fetchCurrentUser()` → `GET /api/auth/me` with Bearer token
7. Backend resolves user, auto-creates or links by `keycloak_sub` / email

### Invite Link
1. Unauthenticated user opens `/join?token=<invite_token>`
2. `JoinComponent` validates via `GET /api/invite-links/validate/{token}` (public)
3. Stores pending token in `localStorage` as `simoops_pending_invite_token`
4. OIDC login flow proceeds
5. After login, `UserService.fetchCurrentUser()` checks `localStorage` → `POST /api/invite-links/accept/{token}`

### Logout
- `AuthService.logout()` → clears `_token`, `localStorage` cleanup → `OidcSecurityService.logoff()` → Keycloak logout → `/login`

## Frontend Methods
- `AuthService.login()` → `OidcSecurityService.authorize()`
- `AuthService.logout()` → `OidcSecurityService.logoff()`
- `AuthService.refreshToken()` → `OidcSecurityService.forceRefreshSession()`
- `AuthService.checkAuthOnInit()` → `OidcSecurityService.checkAuth()` → stores token → `fetchCurrentUser()`
- `AuthGuard.canActivate` → `checkAuthOnInit()` → `true` or `UrlTree['/login']`
- `AuthInterceptor` → attaches Bearer, handles 401 refresh
- `utils/auth-diag.ts::decodeJwtClaims(token)` → extracts `sub`, `email`, `iss`, `exp` without signature verification
- `utils/auth-diag.ts::logAuthDiag(tag, data, level)` → console + fire-and-forget POST to `/api/diag/auth-event` with `keepalive: true`

## OIDC Configuration
```ts
authority: `${window.location.origin}/realms/simoops`,
redirectUrl: `${window.location.origin}/`,
postLogoutRedirectUri: `${window.location.origin}/login`,
clientId: 'simoops-frontend',
scope: 'openid profile email',
responseType: 'code',
silentRenew: true,
useRefreshToken: true,
renewTimeBeforeTokenExpiresInSeconds: 75,
maxIdTokenIatOffsetAllowedInSeconds: 600,
```

## API Interception
- Every HTTP request intercepted by `authInterceptor`
- Attaches: `Authorization: Bearer <access_token>`
- Skipped URLs: `/realms/`, `/.well-known/openid-configuration`
- Interceptor order: `apiErrorInterceptor` → `loggingInterceptor` → `authInterceptor`

## Token Refresh
- `silentRenew: true`, `useRefreshToken: true`, `renewTimeBeforeTokenExpiresInSeconds: 75`
- On 401: `authInterceptor` → deduplicated refresh via `refresh$` Observable → `AuthService.refreshToken()` → `OidcSecurityService.forceRefreshSession()` → retry or logout

## Token Format

### Production
- RS256 JWT from Keycloak
- Claims: `sub` (Keycloak UUID), `email`, `name`
- Validation: `jose.jwt.decode()` with `verify_aud: True`, `verify_iss: False`, `verify_exp: True`
- **Issuer intentionally NOT verified** (Keycloak reachable via different origins)
- JWKS cached 5 minutes; missing `kid` → invalidate cache and retry once

### Test Fallback
- HS256, `settings.test_jwt_secret_key`, only in `environment == "test"`
- Claims: `{ "sub": "<user_id>" }`

## Token Storage
- OIDC tokens managed by `angular-auth-oidc-client` (sessionStorage or in-memory)
- `localStorage` only for: `simoops_pending_invite_token`, `simoops_pending_invite_contractor`, legacy cleanup
- E2E test mode: `window.__SIMOOPS_TEST_TOKEN__` skips OIDC entirely

## Backend Endpoints
- `GET /api/auth/me` → `auth.py::get_me` → returns `UserProfile`
- `POST /api/auth/change-password` → `auth.py::change_password`
- `POST /api/diag/auth-event` → `diag.py::post_auth_event` — unauthenticated telemetry sink for frontend `[AUTH-DIAG]` events
- WebSocket: `WS /ws/entities?token=<jwt>` → `_authenticate(token)` → same `authenticate_token()` as HTTP

## User Resolution
`backend/app/core/auth.py::authenticate_token`:
1. Extract `sub`, `email`, `name`
2. Lookup by `keycloak_sub`
3. Fallback: case-insensitive `email` lookup → link `keycloak_sub`
4. Auto-create if neither found
5. `_accept_pending_invites(email, user.id)`

Rejections:
- Missing `sub` → 401
- Missing `email` for new user → 401
- `is_active == false` → 403

## Roles and Permissions

### Source of Truth
- Keycloak is **pure IDP only** — no realm roles used for app auth
- Backend RBAC via `SiteMembership` table
- Roles: `admin` > `coordinator` > `member` > `viewer` > `client`

### Permission Matrix
| role | permissions |
|------|-------------|
| `viewer` | `entity_view`, `clash_view`, `export` |
| `member` | viewer + `entity_create`, `entity_edit`, `entity_delete`, `planning_submit` |
| `coordinator` | member + `entity_manage_any`, `audit_view`, `data_lock`, `shift_manage`, `contractor_manage`, `site_map_manage`, `layer_manage`, `building_edit`, `clash_rule_manage`, `invite_manage`, `report_manage`, `planning_manage`, `site_settings_basic` |
| `admin` | coordinator + `site_settings` |
| `superadmin` | bypasses all checks (`is_superadmin == true`) |

### Invite Constraints
- Inviter can only assign role at or below own rank

## Contractor Scoping
- `member` / `viewer` have `contractor_id` on `SiteMembership`
- `admin` / `coordinator` see all entities
- Cross-contractor visibility flags on membership or site:
  - `can_view_others_workers`
  - `can_view_others_plant`
  - `can_view_others_zones`

## WebSocket Auth
- Token passed as query parameter: `WS /ws/entities?token=<jwt>`
- Same `authenticate_token()` as HTTP
- Failure: `{"error": "Authentication failed: ..."}` + close code 1008
- After auth: `subscribe` action → `_verify_and_prepare_subscription()` → returns `SubscriptionContext` with role, contractor_id, can_view_others flags

## Context Invalidation
- Backend broadcasts `context_invalidated` when site visibility flags or roles change
- Frontend re-subscribes to force fresh `_verify_and_prepare_subscription`
