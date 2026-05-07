---
service: backend
channel: http
---

# HTTP API

## Auth & Users

| Prefix | Methods | Auth | Notes |
|---|---|---|---|
| `/api/auth/` | GET, POST | Bearer | Profile, change password |
| `/api/users/` | GET | Bearer | Bulk lookup by ID |
| `/api/memberships/` | GET, POST, DELETE | Bearer | Pending approvals |
| `/api/invites/` | GET, POST, DELETE | Bearer | Email invites |
| `/api/invite-links/` | GET, POST, DELETE | Bearer / None | Shareable invite links |
| `/api/diag/auth-event` | POST | None | Telemetry sink for frontend `[AUTH-DIAG]` events |

## Site & Config

| Prefix | Methods | Auth | Notes |
|---|---|---|---|
| `/api/sites/` | GET, POST, PATCH, PUT, DELETE | Bearer / open | Site CRUD, settings, lock; PATCH uses `site_settings` (admin) for planning toggles or `site_settings_basic` (coordinator+) for other fields |
| `/api/site-maps/` | GET, POST | Bearer | Map layers |
| `/api/contractors/` | GET, POST, PATCH, DELETE | Bearer / open | Contractor CRUD |
| `/api/contractors/{id}/logo` | PUT, DELETE | Bearer | Upload/replace/delete contractor logo |
| `/api/contractors/{id}/logo/image` | GET | None (public) | Stream logo bytes with 5min Cache-Control |
| `/api/shifts/` | GET, POST, DELETE | Bearer | Shift scheduling |
| `/api/sites/{id}/label-styles/` | GET, PUT | Bearer | Text label styles |

## Entity CRUD

| Prefix | Methods | Auth | Notes |
|---|---|---|---|
| `/api/workers/` | GET, POST, PATCH, PUT, DELETE | Bearer | Personnel; contractor-scoped |
| `/api/plant/` | GET, POST, PATCH, PUT, DELETE | Bearer | Equipment; schedule groups |
| `/api/deliveries/` | GET, POST, PATCH, DELETE | Bearer | Delivery windows |
| `/api/pois/` | GET, POST, PATCH, DELETE | Bearer | Site markers |
| `/api/text-labels/` | GET, POST, PATCH, DELETE | Bearer | Text annotations |
| `/api/floor-plans/` | GET, POST, PATCH, DELETE | Bearer | GeoTIFF/image upload |
| `/api/smart-groups/` | GET, POST, PATCH, DELETE | Bearer | Per-user filters |

## Planning & Clash

| Prefix | Methods | Auth | Notes |
|---|---|---|---|
| `/api/planning-cycles/` | GET, POST, PATCH | Bearer | Draft → active → archived |
| `/api/clashes/` | GET, POST | Bearer | Detect & resolve; 15s timeout → 504 |
| `/api/clashes/at-time` | GET | Bearer | Historical evaluation; `?involving=<kind>/<uuid>` filter |
| `/api/clash-rules/` | GET, POST, PATCH, DELETE | Bearer | Rule CRUD, DSL, versions |
| `/api/rule-profiles/` | GET, POST, PATCH, DELETE | Bearer | Profile activation, clone |

## Reports & Audit

| Prefix | Methods | Auth | Notes |
|---|---|---|---|
| `/api/reports/` | GET, POST, PATCH, DELETE | Bearer | PDF/DOCX export sessions |
| `/api/exports/` | GET, POST | Bearer | Site PDF/GeoJSON |
| `/api/audit/` | GET, POST | Bearer | Audit log, revert |

## Imports

| Prefix | Methods | Auth | Notes |
|---|---|---|---|
| `/api/import/` | GET, POST | Bearer | CSV/GeoJSON bulk ingest |
| `/api/bundle-import/` | POST | Bearer | .sob bundle |
| `/api/permits/` | GET, POST, DELETE | Bearer / open | XLSX permits; formats public |
| `/api/geometadata/` | GET, POST, PATCH, PUT, DELETE | Bearer | GeoJSON/SHP upload |

## Geometry & Maps

| Prefix | Methods | Auth | Notes |
|---|---|---|---|
| `/api/geometry/` | GET, POST | Bearer | Cut, undo; lock aware |
| `/api/tiles/` | GET | None | Raster, vector, floor-plan |
| `/api/weather/` | GET | Bearer | Site weather forecast |

## System

| Prefix | Methods | Auth | Notes |
|---|---|---|---|
| `/api/health/` | GET | None | Liveness, readiness probes |
| `/api/health/ready` | GET | None | Readiness: DB, S3, Redis, JWKS; configurable thresholds for pending deletes and Redis drops |
| `/api/_test/` | GET, POST | None | Test-only; env-gated |
| `/api/alerts/` | GET, POST, PATCH, DELETE | Bearer | Site alerts |

## Permissions

All Bearer routes validate JWT via `core_auth::authenticate_token` then check
`core_rbac::require_site_permission` or `has_site_permission`. Public (`open`)
endpoints skip auth but may still require `entity_view` for site-scoped data.
