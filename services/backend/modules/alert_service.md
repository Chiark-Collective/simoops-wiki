---
service: backend
summary: "Alert and work group CRUD with contractor visibility"
paths:
  - backend/app/services/entity/alert_service.py
flows: []
touches:
  - services/backend/modules/entity_broadcast_audit.md
  - services/backend/modules/core_rbac.md
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Manages alerts as a paired unit of `Alert` (spatial marker) and `WorkGroup`
(metadata + contractor tags). Coordinators/admins create, update, resolve, and
delete alerts. All site members can view subject to visibility rules.

## Interface
- `alert_service.py::validate_work_group_association(session, work_group_id, site_id, contractor_id, entity_type)` → None
- `alert_service.py::AlertService.list_alerts(user, site_id, include_resolved)` → list[AlertRead]
- `alert_service.py::AlertService.create_alert(user, payload)` → AlertRead
- `alert_service.py::AlertService.get_alert(user, alert_id)` → AlertRead
- `alert_service.py::AlertService.update_alert(user, alert_id, payload)` → AlertRead
- `alert_service.py::AlertService.delete_alert(user, alert_id)` → None
- `alert_service.py::AlertService.resolve_alert(user, alert_id, payload)` → AlertRead
- `alert_service.py::AlertService.unresolve_alert(user, alert_id)` → AlertRead
- `alert_service.py::AlertService.get_activity(user, alert_id)` → list[AlertActivityEntry]

## State
None at module level. All state is persistent (PostGIS).

## Internals
- `create_alert` creates a `WorkGroup` first, flushes to get its ID, then creates the `Alert`
- `_sync_contractors` deletes all existing `WorkGroupContractor` rows and inserts new ones; flush between delete and insert to avoid unique-constraint races
- `_get_contractor_ids_batch` replaces N+1 contractor lookups with a single query for `list_alerts`
- Visibility filtering: `visibility='tagged'` hides the alert from members whose contractor is not tagged, unless privileged (coordinator/admin/superadmin)
- `resolve_alert` sets `WorkGroup.status = resolved` and stamps `Alert.resolved_at`, `resolved_by`, `resolution_comment`
- `unresolve_alert` reverses the above and writes an audit entry
- `get_activity` merges audit entries with associated entity creation events (workers, plants, geometadata features) sorted by timestamp
- `delete_alert` deletes the `WorkGroup` which cascades to `Alert` and contractor tags
- Audit entries use `entity_type="alert"` and `entity_id=alert.id`

## Touches
| resource | how | why |
|---|---|---|
| services/backend/modules/entity_broadcast_audit.md | `_broadcast_event`, `_audit.record` | WS events + audit trail |
| services/backend/modules/core_rbac.md | `require_site_permission` | RBAC checks |
| services/backend/modules/websocket_runtime.md | `ws_manager.broadcast_entity_event` | Real-time alert events |

## Gotchas
- `validate_work_group_association` raises 404 if the work group belongs to a different site — callers must ensure `site_id` matches
- Associating an entity with a resolved or archived work group raises 422
- `_sync_contractors` is a full replacement, not a diff; concurrent edits to contractor tags may race
- `get_activity` queries `Worker`, `Plant`, and `GeometadataFeature` by `work_group_id`; N+1 is avoided because each list is fetched in a single query
