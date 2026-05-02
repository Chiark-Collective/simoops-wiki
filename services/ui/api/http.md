---
service: ui
channel: http
---

# HTTP API

Domain-specific API wrappers under `app/api/`. Each wraps a backend domain. The monolithic `ApiService` façade (`api.service.ts`) delegates to these for backward compatibility.

## Area

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/area.api.ts::AreaApi` | Area CRUD, geometry ops, cut/hole/undo | `POST /areas`, `GET /areas/{id}`, `PATCH /areas/{id}`, `DELETE /areas/{id}`, `POST /areas/{id}/cut`, `POST /areas/{id}/cut-hole`, `POST /areas/{id}/undo-cut` |

## Worker

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/worker.api.ts::WorkerApi` | Worker CRUD, position updates, schedule | `POST /workers`, `GET /workers/{id}`, `PATCH /workers/{id}`, `DELETE /workers/{id}` |

## Plant

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/plant.api.ts::PlantApi` | Plant CRUD, geometry, scheduling | `POST /plants`, `GET /plants/{id}`, `PATCH /plants/{id}`, `DELETE /plants/{id}` |

## Site

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/site.api.ts::SiteApi` | Site CRUD, maps, contractors, shifts, invites | `GET /sites`, `POST /sites`, `GET /sites/{id}`, `PATCH /sites/{id}`, `DELETE /sites/{id}`, `GET /sites/{id}/maps`, `POST /sites/{id}/maps` |

## Auth

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/auth.api.ts::AuthApi` | User profile, public users, refresh context | `GET /auth/me`, `GET /auth/users/public`, `POST /auth/refresh-context` |

## Clash

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/clash.api.ts::ClashApi` | Clash detection, rules, profiles, resolution | `GET /clashes`, `POST /clashes/resolve`, `GET /clash-rules`, `POST /clash-rules`, `GET /rule-profiles` |

## Geometry

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/geometry.api.ts::GeometryApi` | Geometry history, vertex ops | `GET /geometry/history`, `POST /geometry/vertex-op` |

## Planning

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/planning.api.ts::PlanningApi` | Planning cycles, submissions, compare, baseline import | `GET /planning/cycles`, `POST /planning/cycles`, `POST /planning/submit`, `POST /planning/compare`, `POST /planning/import-baseline` |

## Report

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/report.api.ts::ReportApi` | Templates, sessions, export | `GET /reports/templates`, `POST /reports/sessions`, `GET /reports/sessions/{id}`, `POST /reports/sessions/{id}/export` |

## Revision

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/revision.api.ts::RevisionApi` | Historical snapshots, audit log | `GET /revisions/snapshot`, `GET /revisions/audit-log` |

## Weather

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/weather.api.ts::WeatherApi` | Weather forecasts, sun times | `GET /weather/forecast` |

## Export

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/export.api.ts::ExportApi` | Entity export, presigned URLs | `POST /export`, `GET /export/presigned` |

## Geometadata

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/geometadata.api.ts::GeometadataApi` | Geometadata layers, features, uploads | `GET /geometadata/layers`, `POST /geometadata/layers`, `POST /geometadata/upload` |

## Entity Support

| Symbol | What | Backend endpoint |
|---|---|---|
| `api/entity-support.api.ts::EntitySupportApi` | Bulk ops, duplicates, search, locks | `POST /entities/bulk`, `POST /entities/duplicate`, `GET /entities/search`, `POST /entities/lock` |
## Interceptors

| Symbol | Order | What |
|---|---|---|
| `api-error.interceptor.ts::apiErrorInterceptor` | Outermost | Transforms `HttpErrorResponse` → `ApiError` |
| `logging.interceptor.ts::loggingInterceptor` | Middle | Logs requests, timing, status |
| `auth.interceptor.ts::authInterceptor` | Innermost | Attaches bearer token; handles 401 refresh |
