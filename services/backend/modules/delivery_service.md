---
service: backend
summary: "Delivery CRUD with plan-state tombstones and cycle tagging"
paths:
  - backend/app/services/entity/delivery_service.py
flows: []
touches:
  - services/backend/modules/entity_broadcast_audit.md
  - services/backend/modules/core_rbac.md
  - services/backend/modules/data_lock.md
  - services/backend/modules/planning_cycle.md
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Orchestrates delivery CRUD as a standalone service (not via `EntityServiceBase`).
Deliveries are informational scheduling entities with a scheduled window. They do
not participate in clash detection.

## Interface
- `delivery_service.py::DeliveryService.list_deliveries(user, site_id, query_start, query_end)` → list[DeliveryRead]
- `delivery_service.py::DeliveryService.create_delivery(user, payload)` → DeliveryRead
- `delivery_service.py::DeliveryService.update_delivery(user, delivery_id, payload)` → DeliveryRead
- `delivery_service.py::DeliveryService.delete_delivery(user, delivery_id)` → None
- `delivery_service.py::DeliveryService.restore_delivery(user, delivery_id)` → DeliveryRead

## State
None at module level. All state is persistent (PostGIS).

## Internals
- `list_deliveries` applies temporal overlap: point-in-time deliveries (`scheduled_end` IS NULL) match if `scheduled_start` falls inside the query range; interval deliveries use standard overlap
- `create_delivery` tags the delivery with a planning cycle via `CycleService.resolve_cycle_tag_for_create`
- `update_delivery` reevaluates cycle membership via `reevaluate_cycle_membership` if the scheduled window moves
- `delete_delivery` tombstones planned rows (`plan_state='planned'`) and hard-deletes others
- `restore_delivery` clears `tombstoned_at` and re-broadcasts as `entity_created`
- Contractor visibility uses the `workers` cross-contractor toggle (`ENTITY_TYPE_WORKERS`)
- Data lock checked against `scheduled_end` or `scheduled_start` (whichever is present)
- Permit links extracted from `extra` and counts decremented on delete (reuses permit_import helpers)

## Touches
| resource | how | why |
|---|---|---|
| services/backend/modules/entity_broadcast_audit.md | `_broadcast_delivery_event`, `_audit.record` | WS events + audit trail |
| services/backend/modules/core_rbac.md | `require_site_permission`, `_require_contractor_access` | RBAC + contractor scoping |
| services/backend/modules/data_lock.md | `require_not_locked` | Blocks edits inside locked periods |
| services/backend/modules/planning_cycle.md | `CycleService.resolve_cycle_tag_for_create`, `reevaluate_cycle_membership` | Cycle tagging + window membership |
| services/backend/modules/websocket_runtime.md | `ws_manager.broadcast_entity_event` | Real-time delivery events |

## Gotchas
- Deliveries do NOT have `work_group_id`; they are purely informational/planning
- `list_deliveries` uses `ENTITY_TYPE_WORKERS` for contractor visibility because deliveries are scheduling artefacts tied to personnel
- `restore_delivery` requires `entity_delete` permission (same as restore on plant/worker)
- `update_delivery` mutates `extra` to inject `updated_by_contractor` metadata; partial updates to `extra` from the payload overwrite the whole dict
- Permit count decrement on delete is conditional on `extract_permit_link` finding a link in `extra`
