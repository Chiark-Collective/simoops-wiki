---
service: backend
summary: "Point of Interest CRUD for site-wide informational markers"
paths:
  - backend/app/services/entity/poi_service.py
flows: []
touches:
  - services/backend/modules/entity_broadcast_audit.md
  - services/backend/modules/core_rbac.md
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Manages Points of Interest (PoI) as site-wide permanent informational markers.
PoIs have no temporal model and do not participate in clash detection. Only
coordinators/admins can create, update, or delete them.

## Interface
- `poi_service.py::PoIService.list_pois(user, site_id)` → list[PoIRead]
- `poi_service.py::PoIService.create_poi(user, payload)` → PoIRead
- `poi_service.py::PoIService.update_poi(user, poi_id, payload)` → PoIRead
- `poi_service.py::PoIService.delete_poi(user, poi_id)` → None

## State
None at module level. All state is persistent (PostGIS).

## Internals
- `_poi_to_read` converts WKB position to WGS84 `PositionLonLat` via `wkb_to_point` → `point_to_wgs84`
- `poi_type` defaults to `PoiType.generic` in the schema; the model also has a server default
- All authenticated site members can list PoIs; CUD is gated by `Permission.entity_manage_any`
- Audit entries use `entity_type="poi"` with the PoI title as `entity_label`
- Deletion hard-deletes the row (no tombstone mechanism because PoIs have no planning cycle)

## Touches
| resource | how | why |
|---|---|---|
| services/backend/modules/entity_broadcast_audit.md | `_broadcast_poi_event`, `_audit.record` | WS events + audit trail |
| services/backend/modules/core_rbac.md | `require_site_permission` | RBAC checks |
| services/backend/modules/websocket_runtime.md | `ws_manager.broadcast_entity_event` | Real-time PoI events |

## Gotchas
- PoIs have no contractor association; all site members see every PoI
- `position_wgs84` is optional in the model but typically provided by the frontend
- No data lock check because PoIs are permanent site fixtures, not time-bound entities
