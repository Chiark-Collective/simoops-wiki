---
trigger: { channel: route, ref: "/login" }
services: [ui, backend]
contracts: [ui-backend/auth-contract]
external: [keycloak]
---

## Trigger
User navigates to `/login` or is redirected by `authGuard`.

## Steps
1. `app.routes.ts::routes` — `{ path: 'login', component: LoginComponent }` resolves.
2. `login/login.component.ts::LoginComponent.ngOnInit` — if `auth.isAuthenticated()` is true, redirects to `/sites`.
3. `login/login.component.ts::LoginComponent.signIn` — calls `auth.login()`.
4. `auth.service.ts::AuthService.login` — `oidc.authorize()` initiates Keycloak redirect. See [services/ui/modules/auth.md](../modules/auth.md) for OIDC details.
5. Keycloak authenticates user and redirects back to `/` with authorization code. See [contracts/ui-backend/auth-contract.md](../../../contracts/ui-backend/auth-contract.md) for token format.
6. `app.routes.ts::routes` — root `/` requires `authGuard` then `siteSelectedGuard`.
7. `auth.guard.ts::authGuard` — calls `auth.checkAuthOnInit()`.
8. `auth.service.ts::AuthService.checkAuthOnInit` — `oidc.checkAuth()` exchanges code for token; on success sets `_token` and chains into `fetchCurrentUser`.
9. `services/user.service.ts::UserService.fetchCurrentUser` — calls `api.getCurrentUser()`. If `localStorage` contains `simoops_pending_invite_token`, removes both token and contractor keys, then calls `api.acceptInviteLink`; on active membership re-fetches profile.
10. `site-selected.guard.ts::siteSelectedGuard` — checks `siteContext.selectedSite`; if falsy, calls `tryRestoreSite()`; if still no site, redirects to `/sites`.
11. `site-selection/site-selection.component.ts::SiteSelectionComponent.ngOnInit` — `siteContext.loadSites()`; if only one site, auto-selects via `selectSite()`.
12. `site-selection/site-selection.component.ts::SiteSelectionComponent.selectSite` — calls `siteContext.selectSite(site)` then navigates to `/`.
13. `services/site-context.service.ts::SiteContextService.selectSite` — `_selectedSite.next(site)` → `timezone.setSiteTz` → `temporalContext.setSelectedShift(null)` → resets shifts/contractors/maps → `userService.setActiveSite` → `localStorage.setItem(LAST_SITE_KEY, site.id)` → `temporalContext.setSelectedDate(timeUtil.getTodayInTimezone(site.timezone || 'UTC'))` → `loadShifts(site.id)`, `loadContractors(site.id)`, `loadSiteMaps(site.id)`. See [services/ui/modules/site-admin.md](../modules/site-admin.md) for full cascade.
14. `dashboard/dashboard.component.ts::DashboardComponent.ngOnInit` — `bootstrapWiring.wireOnInitSubscriptions()`.
15. `services/dashboard-bootstrap-wiring.service.ts::DashboardBootstrapWiringService.wireOnInitSubscriptions` — `dataLoad.setupContextLoading()`.
16. `services/data-load.service.ts::DataLoadService.setupContextLoading` — `combineLatest([selectedSite$, requiredFetches$, appMode$])` → deduped `forkJoin` loads areas, roads, tokens, plants, deliveries, POIs, alerts, text labels.

## Side effects
- Keycloak OIDC authorization redirect.
- `localStorage.removeItem('simoops_pending_invite_token')` and `removeItem('simoops_pending_invite_contractor')`.
- `localStorage.setItem('simoops_last_site_id', site.id)`.
- HTTP calls: `GET /api/auth/me`, `POST /api/invite-links/accept/{token}`, `GET /api/sites`, `GET /api/shifts`, `GET /api/contractors`, `GET /api/site-maps`, plus entity loads (areas, roads, tokens, plants, deliveries, POIs, alerts, text labels).
- BehaviorSubject emissions: `_selectedSite`, `_shifts`, `_contractors`, `_siteMaps`, `_selectedSiteMap`.

## Failure modes
- OIDC redirect fails or user cancels: `authGuard` returns `UrlTree['/login']`.
- `checkAuthOnInit` short-circuits in test mode (`_token && _initialized` already set).
- `UserService.fetchCurrentUser` removes pending invite token from `localStorage` before `api.acceptInviteLink` resolves; API failure loses the token permanently.
- `siteSelectedGuard` auto-restores from `localStorage` via `tryRestoreSite()` if possible.
- `AuthService` reads `window.__SIMOOPS_TEST_TOKEN__` once at construction; injecting after bootstrap has no effect.
- Dashboard data-load `forkJoin` failure shows toast and returns `null`; partial data may render.
