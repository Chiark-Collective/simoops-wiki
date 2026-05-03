---
service: ui
summary: Bootstrap, routing, guards, and HTTP interceptors for the SimOops Angular app.
paths:
  - app.config.ts
  - app.component.ts
  - app.component.html
  - app.routes.ts
  - auth.guard.ts
  - site-selected.guard.ts
  - auth.interceptor.ts
  - api-error.interceptor.ts
  - logging.interceptor.ts
flows:
  - OIDC auth code flow with silent renew and refresh tokens
  - 401 burst queue: concurrent 401s subscribe to a single shared token refresh, then retry individually
  - Site restore flow: guard checks memory → localStorage → redirect to /sites
touches:
  - localStorage (site context restoration)
  - Keycloak/OIDC authority endpoints
  - HTTP client (outgoing API requests)
  - console / window.simoopsLogs (via ConsoleLogService)
external:
  - angular-auth-oidc-client
  - AuthService
  - SiteContextService
  - MessageService
  - ConsoleLogService
  - createLogger
  - ApiError
last_verified_commit: f9606469ce367229c5c91e03c3ba917779015030
---

## Purpose
Configures the Angular application bootstrap with zoneless change detection, OIDC authentication via angular-auth-oidc-client, HTTP interceptors, and top-level routing. The root component is a thin shell that delegates all page rendering to the router outlet.

## Interface
- `app.config.ts::appConfig` — `ApplicationConfig` exported to `bootstrapApplication`. Registers `provideZonelessChangeDetection`, `provideRouter`, `provideHttpClient(withInterceptors([...]))`, conditional `provideAuth` for Keycloak OIDC, and an `APP_INITIALIZER` that starts `ConsoleLogService`.
- `app.component.ts::AppComponent` — Root component with selector `app-root`; renders `<router-outlet>`.
- `app.routes.ts::routes` — Top-level `Routes` array: `/login`, `/unauthorized` → `/login`, `/join` (lazy), `/sites` (lazy, `authGuard`), `/dev/weather-ribbon` (lazy), and root `/` (`DashboardComponent`, guarded by `authGuard` + `siteSelectedGuard`).
- `auth.guard.ts::authGuard` — `CanActivateFn` that waits for OIDC init via `AuthService.checkAuthOnInit()` and redirects unauthenticated users to `/login`.
- `site-selected.guard.ts::siteSelectedGuard` — `CanActivateFn` that checks `SiteContextService` for a selected site; attempts `tryRestoreSite()` from localStorage, otherwise redirects to `/sites`.
- `auth.interceptor.ts::authInterceptor` — `HttpInterceptorFn` that attaches the OIDC bearer token to outgoing API requests, skips Keycloak URLs, and handles 401 by queuing retries behind a single token refresh via `shareReplay`.
- `api-error.interceptor.ts::apiErrorInterceptor` — `HttpInterceptorFn` that sits outermost and transforms `HttpErrorResponse` into `ApiError` for all non-Keycloak requests.
- `logging.interceptor.ts::loggingInterceptor` — `HttpInterceptorFn` that logs request/response summaries, timing, status codes, and errors via `createLogger('HTTP')`; skips static assets.

## State
`auth.interceptor.ts` maintains module-scoped mutable state:
- `refresh$: Observable<string | null> | null` — Handle to the in-flight token refresh stream. While non-null, every 401-triggered interceptor invocation subscribes to the same Observable rather than initiating a new refresh. Reset to `null` via `finalize` once the stream completes or errors.

## Internals

**Bootstrap ordering**
`appConfig` registers providers in this order: zoneless change detection → router → HTTP client with interceptors → conditional OIDC auth → `APP_INITIALIZER` for console logging. `provideHttpClient` loads interceptors left-to-right in the array: `[apiErrorInterceptor, loggingInterceptor, authInterceptor]`.

**Interceptor stack order**
Array order determines wrapping order. `apiErrorInterceptor` is outermost: it sees every downstream error first, but because it wraps the others, its `catchError` runs last in the error-propagation chain.
- A 401 response travels through `authInterceptor` first (catches 401, triggers refresh, retries).
- If the retry also fails, the error bubbles back up through `loggingInterceptor` (logs the failure), then finally reaches `apiErrorInterceptor` (wraps in `ApiError`).
- `loggingInterceptor` sits in the middle, so it observes the original request and the final response (or error) after auth retry logic has run.

**401 refresh queue**
When `authInterceptor` catches a 401:
1. If `auth.isLoggingOut` is true, propagate immediately.
2. Otherwise call `getRefresh()`, which checks the module-level `refresh$` handle.
3. If `refresh$` is null, `auth.refreshToken()` is invoked and piped through `tap` (side-effects: logout/navigate/message on null or error), `catchError(() => of(null))`, `finalize(() => refresh$ = null)`, and `shareReplay({ bufferSize: 1, refCount: false })`.
4. Every concurrent 401 subscriber receives the same replayed result via `shareReplay`. On success, each subscriber retries its own request with the new token. On failure, each propagates the original `HttpErrorResponse`.

**Guard semantics**
`authGuard` returns an Observable that resolves only after OIDC initialization completes (`auth.checkAuthOnInit()`). Navigation does not proceed until the OIDC library has finished its internal discovery/token-check cycle.
`siteSelectedGuard` is synchronous for the happy path (`siteContext.selectedSite` truthy). It becomes async only in the sense that `tryRestoreSite()` may read localStorage, but the guard itself does not return an Observable.

**OIDC configuration**
Enabled conditionally via `environment.oidc.enabled`. Config sets `silentRenew: true`, `useRefreshToken: true`, `renewTimeBeforeTokenExpiresInSeconds: 75`, and `maxIdTokenIatOffsetAllowedInSeconds: 600`.

## Touches
- localStorage (via `SiteContextService.tryRestoreSite()`)
- Keycloak/OIDC authority endpoints (`/realms/`, `/.well-known/openid-configuration`)
- HTTP client (all API traffic)
- `window.simoopsLogs` / console (via `ConsoleLogService` and `createLogger`)

## Gotchas
- `apiErrorInterceptor` skips Keycloak URLs but uses a simple string-match (`includes('/realms/') || includes('/openid-configuration')`). If the API ever exposes paths containing these substrings, errors from those routes will not be wrapped in `ApiError`.
- `loggingInterceptor` skips `/assets/` and `.json` files unless the URL contains `/api/`. This heuristic may miss or include unexpected routes.
- `authInterceptor` also skips Keycloak URLs by substring match. More importantly, it injects `AuthService` inside the interceptor function rather than at module scope; while this avoids the circular-DI issue during OIDC bootstrap, it means each invocation re-resolves the service from the injector.
- The `refresh$` queue is module-scoped and shared across all HTTP requests. If a token refresh produces `null`, the side-effects (logout, navigate, message) fire once per burst via `tap`, but every queued request individually propagates the original 401 error.
- `authGuard` waits for `checkAuthOnInit()`, which is an Observable. If the OIDC init hangs, the route transition never completes.
- `siteSelectedGuard` redirects to `/sites` when no site is selected, but `/sites` itself is protected by `authGuard`. An unauthenticated user hitting `/` is first blocked by `authGuard` and never reaches `siteSelectedGuard`.
