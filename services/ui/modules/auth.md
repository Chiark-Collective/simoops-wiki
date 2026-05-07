---
service: ui
summary: OIDC authentication, user profile, and auth-related page components.
paths:
  - auth.service.ts
  - services/user.service.ts
  - login/login.component.ts
  - join/join.component.ts
  - site-selection/site-selection.component.ts
flows:
  - OIDC login/logout
  - Invite join (sign-in + register)
  - Site selection
touches:
  - localStorage
  - window.__SIMOOPS_TEST_TOKEN__
  - Keycloak
  - /api/auth/me
  - SiteContextService
external:
  - angular-auth-oidc-client
  - Keycloak
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose
Wraps `angular-auth-oidc-client` for Keycloak OIDC login/logout and token lifecycle, manages the current user's profile and site-level permissions, and hosts the login, invite-join, and site-selection pages.

## Interface
- `auth.service.ts::AuthService` — Injectable root service wrapping `OidcSecurityService`. Exposes `token`, `isAuthenticated()`, `isAuthenticated$()`, `isTestMode`, `isLoggingOut`, `login()`, `logout()`, `refreshToken()`, and `checkAuthOnInit()`. Supports Playwright test-token injection via `window.__SIMOOPS_TEST_TOKEN__`. Integrated with `decodeJwtClaims` and `logAuthDiag` for diagnostic logging.
- `utils/auth-diag.ts::decodeJwtClaims(token)` → `JwtClaims | null` — extracts `sub`, `email`, `iss`, `exp` from JWT without signature verification; drops all other claims
- `utils/auth-diag.ts::logAuthDiag(tag, data, level)` — emits `[AUTH-DIAG]` to console AND fire-and-forget POSTs to `/api/diag/auth-event` with `keepalive: true`
- `services/user.service.ts::UserService` — Injectable root service that fetches the user profile from `/api/auth/me`, handles pending invite acceptance post-login, and provides synchronous role/permission checks (`isAdmin`, `isCoordinatorOrAbove`, `isMember`, `canEditBuildings`, `canEditPlantEntity`, etc.).
- `login/login.component.ts::LoginComponent` — Standalone page component with a "Sign in" button that triggers `AuthService.login()`. Auto-redirects authenticated users to `/sites`.
- `join/join.component.ts::JoinComponent` — Standalone invite-link landing page. Validates the invite token, supports registration for new users, sign-in-and-join for existing users, and direct join when already authenticated. Stores pending invite state in `localStorage` for post-OIDC acceptance.
- `site-selection/site-selection.component.ts::SiteSelectionComponent` — Standalone page that displays authorized sites in a carousel with map thumbnails and keyboard navigation. Auto-selects a single site; otherwise lets the user pick and persists the choice via `SiteContextService`. Pre-focuses carousel on last-visited site.

## State
- `auth.service.ts::AuthService` maintains `_token` (`string | null`), `_initialized` (`boolean`), `_loggingOut` (`boolean`), `_testMode` (`boolean`), and `_lastDiagSub` (`string | null` for identity-flip detection).
- `services/user.service.ts::UserService` maintains `_currentUser` (`BehaviorSubject<UserProfile | null>`), `_loading` (`BehaviorSubject<boolean>`), `_error` (`BehaviorSubject<string | null>`), `_activeSiteId` (`BehaviorSubject<string | null>`), and `_initialized` (`boolean`).
- `site-selection/site-selection.component.ts::SiteSelectionComponent` tracks `sites`, `focusedIndex`, `thumbnailFailed` (`Set<string>`), and `containerWidth` for carousel layout.
- Invariants:
- `_testMode === true` ⟂ `AuthService` never touches the OIDC library (`checkAuthOnInit` short-circuits, `refreshToken` returns `of(null)`).
- `_loggingOut === true` ⟂ repeated `logout()` calls are no-ops.
- `!_initialized` in `UserService` → `isCoordinatorOrAbove()` returns `false` (deny-until-verified).
- `activeMembership` is derived from `_currentUser` and `_activeSiteId` → stale if site changes without calling `setActiveSite()`.
- Identity-flip detection: `isAuthenticated$` subscription compares `sub` on silent renew; mismatch logs `[AUTH-DIAG] !! identity flipped` at warn level

## Internals
`AuthService` constructor reads `window.__SIMOOPS_TEST_TOKEN__` once. If present, it skips OIDC entirely, stores the token in `_token`, and defers `userService.fetchCurrentUser()` via `setTimeout` to break a construction-time circular dependency with the HTTP interceptor. OIDC initialization is deliberately deferred to `checkAuthOnInit()` (called by the auth guard) for the same reason.

`checkAuthOnInit()` short-circuits when `_token` and `_initialized` are already set. Otherwise it calls `oidc.checkAuth()`. On success it writes `result.accessToken` to `_token` and subscribes to `oidc.isAuthenticated$` with `takeUntilDestroyed` to keep `_token` synchronized across silent refreshes. It then chains `userService.fetchCurrentUser()`.

`refreshToken()` delegates to `oidc.forceRefreshSession()` and updates `_token` with the new access token. In test mode it returns `of(null)`.

`logout()` sets `_loggingOut`, clears `_token`, removes `simoops_token` from `localStorage`, deletes `window.__SIMOOPS_TEST_TOKEN__`, calls `userService.clearUser()`, and finally issues the OIDC logoff request.

`UserService.fetchCurrentUser()` calls `api.getCurrentUser()`. After the profile arrives it checks `localStorage` for `simoops_pending_invite_token` (and optional contractor). If found, it removes the keys immediately and calls `api.acceptInviteLink()`. A `pending_approval` response preserves the original profile; any other active status triggers a second `getCurrentUser()` call so that new site memberships are reflected in `_currentUser`.

Permission methods are synchronous and keyed to `activeMembership`, which is computed from the current `_currentUser.value` and `_activeSiteId.value`. `setActiveSite()` is the only intended mutator for the active site context.

`JoinComponent` reads the invite `token` from the query string on init and validates it via `api.validateInviteLink()`. `signInAndJoin()` writes the token (and selected contractor) to `localStorage` before calling `auth.login()`. After the OIDC redirect, `UserService.fetchCurrentUser()` consumes those keys. If the user is already authenticated, `joinSite()` calls `api.acceptInviteLink()` directly and navigates to `/` on success or shows the `pending` view when membership requires approval.

`SiteSelectionComponent` loads sites via `siteContext.loadSites()`. Zero sites → empty state. One site → immediate `selectSite()` + navigation to `/`. Multiple sites → carousel with pre-focused last visited site (`siteContext.getLastSelectedSiteId()`). Keyboard navigation (ArrowLeft, ArrowRight, Enter) is bound to `window:keydown`. Carousel translation uses a hard-coded card width of `340px` and a container width measured after view init via `setTimeout` to avoid `ExpressionChangedAfterItHasBeenCheckedError`.

## Touches
- `localStorage` keys: `simoops_token`, `simoops_pending_invite_token`, `simoops_pending_invite_contractor`.
- `window.__SIMOOPS_TEST_TOKEN__`.
- Keycloak (via `angular-auth-oidc-client`).
- `/api/auth/me` and invite endpoints (validation, acceptance, registration).
- `SiteContextService`.

## Gotchas
- ! `window.__SIMOOPS_TEST_TOKEN__` is read once in the `AuthService` constructor. Injecting it after bootstrap has no effect.
- `AuthService` avoids OIDC initialization in its constructor to prevent a circular dependency (`AuthService → HTTP → interceptor → AuthService`). `checkAuthOnInit()` must be invoked by the auth guard before any authenticated HTTP request.
- ! `UserService.fetchCurrentUser()` removes the pending invite token from `localStorage` before the accept API call resolves. If the API fails, the token is lost and the user must re-enter the invite link.
- `isCoordinatorOrAbove()` returns `false` until the first profile fetch completes. Guards or UI that rely on it during the initial load will see a transient deny state.
- All permission checks derive from `activeMembership`, which depends on `_activeSiteId`. Failing to call `setActiveSite()` after a site switch ⇒ stale or null permissions.
- `JoinComponent` declares an `autoRedirectTimer` but never schedules it. It is dead code.
- `SiteSelectionComponent` calls `selectSite()` synchronously and then navigates. If `SiteContextService.selectSite()` throws, the navigation still occurs and the app may enter an inconsistent state.
