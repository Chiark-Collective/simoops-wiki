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
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
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
