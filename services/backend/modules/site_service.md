---
service: backend
summary: "Site-level ops: cascade data nuke, default shifts, and settings"
paths:
  - backend/app/services/site_service.py
  - backend/app/api/routes/sites.py
flows: []
touches:
  - infra/data-stores
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Site-wide operations that don't fit a focused service: wipe operational data
while preserving the site row, seed canonical shifts, manage report branding,
and enforce the data-lock boundary.

## Interface
- `services/site_service.py::create_default_shifts(session, site_id)` → list[Shift]
- `services/site_service.py::nuke_site_data(session, site_id)` → dict[str, int]
- `api/routes/sites.py::list_sites_public(session)` → list[SitePublic]
- `api/routes/sites.py::list_sites(session, user)` → list[SiteRead]
- `api/routes/sites.py::get_site(site_id, session, user)` → SiteRead
- `api/routes/sites.py::update_site(site_id, payload, session, user, audit)` → SiteRead
- `api/routes/sites.py::set_data_lock(site_id, payload, session, user, audit)` → DataLockResponse
- `api/routes/sites.py::get_snapshot_revision_summary(site_id, user, session, at)` → SnapshotRevisionSummary
- `api/routes/sites.py::nuke_site_data(site_id, session, user, confirmation)` → dict
- `api/routes/sites.py::upload_report_logo(site_id, file, session, user)` → dict
- `api/routes/sites.py::delete_report_logo(site_id, session, user)` → Response

## State
None. Stateless service and routes.

## Internals
- `nuke_site_data` deletes in child-to-parent order: Workers, Plants → Shifts → GeometadataFeatures → GeometadataLayers → SiteMaps
- Contractors and the Site row survive nuke
- `create_default_shifts` adds to session but does **not** commit; caller controls transaction boundary
- `nuke_site_data` commits internally and recreates the canonical Day/Back/Night shifts via `create_default_shifts`
- `update_site` detects visibility flag changes and calls `websocket_runtime::invalidate_subscription_context` to force WS clients to re-subscribe
- Data lock endpoint uses `data_lock::is_user_admin_or_superadmin` to restrict clearing or moving the lock backward
- Report logo upload validates MIME type against `ALLOWED_LOGO_TYPES` and enforces 2 MB size limit; old logo is deleted from storage after successful replacement

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | SQLModel CRUD on Site, Worker, Plant, Shift, GeometadataLayer, GeometadataFeature, SiteMap | Persistent state for nuke, settings, and branding |
| modules/websocket_runtime.md | `invalidate_subscription_context` on visibility flag mutation | Refresh stale cached permission context |
| modules/data_lock.md | `is_user_admin_or_superadmin` for lock privilege check | Only admins can clear or roll back lock boundary |

## Gotchas
- `nuke_site_data` requires confirmation string `"Kenny Loggins"`; typo ⇒ 400
- `create_default_shifts` does not commit; `nuke_site_data` does — mismatch if composed incorrectly
- Visibility flag changes trigger WS context invalidation, but clients may operate with stale permissions until they re-subscribe
- Moving data lock backward or clearing it requires admin role; coordinators can only advance it
