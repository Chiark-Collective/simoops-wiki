---
service: ui
summary: OIDC authentication, user profile, and auth-related page components.
paths:
  - auth.service.ts
  - services/user.service.ts
  - login/login.component.ts
  - join/join.component.ts
  - site-selection/site-selection.component.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Wraps angular-auth-oidc-client for Keycloak OIDC login/logout and token lifecycle, manages the current user's profile and site-level permissions, and hosts the login, invite-join, and site-selection pages.

## Interface
- `auth.service.ts::AuthService` — Injectable root service wrapping `OidcSecurityService`. Exposes `token`, `isAuthenticated()`, `isTestMode`, `isLoggingOut`, `login()`, `logout()`, `refreshToken()`, and `checkAuthOnInit()`. Supports Playwright test-token injection via `window.__SIMOOPS_TEST_TOKEN__`.
- `services/user.service.ts::UserService` — Injectable root service that fetches the user profile from `/api/auth/me`, handles pending invite acceptance post-login, and provides synchronous role/permission checks (`isAdmin`, `isCoordinatorOrAbove`, `isMember`, `canEditBuildings`, `canEditPlantEntity`, etc.).
- `login/login.component.ts::LoginComponent` — Standalone page component with a "Sign in" button that triggers `AuthService.login()`. Auto-redirects authenticated users to `/sites`.
- `join/join.component.ts::JoinComponent` — Standalone invite-link landing page. Validates the invite token, supports registration for new users, sign-in-and-join for existing users, and direct join when already authenticated. Stores pending invite state in `localStorage` for post-OIDC acceptance.
- `site-selection/site-selection.component.ts::SiteSelectionComponent` — Standalone page that displays authorized sites in a carousel with map thumbnails and keyboard navigation. Auto-selects a single site; otherwise lets the user pick and persists the choice via `SiteContextService`.
