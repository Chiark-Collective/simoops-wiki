---
service: backend
summary: "Text label CRUD for site-wide map annotations"
paths:
  - backend/app/services/entity/text_label_service.py
flows: []
touches:
  - services/backend/modules/entity_broadcast_audit.md
  - services/backend/modules/core_rbac.md
  - services/backend/modules/websocket_runtime.md
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Manages TextLabel entities as site-wide permanent text annotations on the map.
Text labels have no temporal model and do not participate in clash detection.
Only coordinators/admins can create, update, or delete them.

## Interface
- `text_label_service.py::TextLabelService.list_text_labels(user, site_id)` → list[TextLabelRead]
- `text_label_service.py::TextLabelService.create_text_label(user, payload)` → TextLabelRead
- `text_label_service.py::TextLabelService.update_text_label(user, label_id, payload)` → TextLabelRead
- `text_label_service.py::TextLabelService.delete_text_label(user, label_id)` → None

## State
None at module level. All state is persistent (PostGIS).

## Internals
- `_text_label_to_read` converts WKB position to WGS84 `PositionLonLat` via `wkb_to_point` → `point_to_wgs84`
- `create_text_label` converts incoming `PositionLonLat` to WKB (srid=3857) via `lonlat_to_point` → `point_to_wkb`
- All authenticated site members can list text labels; CUD is gated by `Permission.entity_manage_any`
- Audit entries use `entity_type="text_label"` with the label title as `entity_label`
- Deletion hard-deletes the row (no tombstone mechanism because text labels have no planning cycle)
- `delete_text_label` broadcasts `entity_deleted` directly via `ws_manager` rather than `_broadcast_event`

## Touches
| resource | how | why |
|---|---|---|
| services/backend/modules/entity_broadcast_audit.md | `_audit.record` | Audit trail on every mutation |
| services/backend/modules/core_rbac.md | `require_site_permission` | RBAC checks |
| services/backend/modules/websocket_runtime.md | `ws_manager.broadcast_entity_event` | Real-time label events |

## Gotchas
- Text labels have no contractor association; all site members see every label
- `position_wgs84` is optional in the model but typically provided by the frontend
- No data lock check because text labels are permanent site fixtures, not time-bound entities
- `delete_text_label` bypasses `_broadcast_event` and calls `ws_manager.broadcast_entity_event` directly
