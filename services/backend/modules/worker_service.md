---
service: backend
summary: "Worker CRUD with colour state and batch delete"
paths:
  - backend/app/services/entity/worker_service.py
flows:
  - services/backend/flows/entity_creation.md
  - services/backend/flows/entity_update.md
touches:
  - services/backend/modules/entity_service.md
  - services/backend/modules/entity_schedule.md
  - services/backend/modules/entity_broadcast_audit.md
  - services/backend/modules/core_rbac.md
  - services/backend/modules/data_lock.md
  - services/backend/modules/clash_proximity.md
  - services/backend/modules/planning_cycle.md
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Orchestrates worker CRUD via `EntityServiceBase`. Resolves positions from metres,
WGS84, or pixel coordinates. Computes colour state for clash proximity. Supports
batch deletion and schedule operations.

## Interface
- `worker_service.py::WorkerService.create_worker(user, payload)` → WorkerRead
- `worker_service.py::WorkerService.update_worker(user, worker_id, payload)` → WorkerRead
- `worker_service.py::WorkerService.delete_worker(user, worker_id)` → None
- `worker_service.py::WorkerService.restore_worker(user, worker_id)` → WorkerRead
- `worker_service.py::WorkerService.list_workers(user, site_id, query_start, query_end)` → list[WorkerRead]
- `worker_service.py::WorkerService.batch_delete_workers(user, site_id, query_start, query_end)` → int
- `worker_service.py::WorkerService.copy_workers_from_range(user, payload)` → WorkerCopyResponse
- `worker_service.py::WorkerService.create_worker_schedule(user, payload)` → ScheduleCreateResponse
- `worker_service.py::WorkerService.delete_worker_schedule_group(user, group_id)` → None
- `worker_service.py::WorkerService.get_worker_schedule_group(user, group_id)` → list[WorkerRead]
- `worker_service.py::WorkerService.update_worker_schedule_group(user, group_id, payload)` → list[WorkerRead]
- `worker_service.py::WorkerService.reconcile_worker_schedule_group(user, group_id, request)` → ScheduleReconcileResponse
- `worker_service.py::WorkerService.convert_worker_to_schedule(user, worker_id, request)` → ScheduleCreateResponse

## State
None at module level. All state is persistent (PostGIS).

## Internals
- `_resolve_position` accepts `position_m`, `position_wgs84`, or `position_px` (requires calibrated `site_map_id`)
- `_entity_to_read` delegates to `clash/proximity.py::worker_to_read` for full colour state computation
- `list_workers` uses `workers_to_read_lite` to skip colour computation; frontend derives severity from live clash list via `buildEntitySeverityMap`
- `get_worker_schedule_group` also uses lite serialization because the schedule editor only needs dates/times
- `_entities_to_read_batch` uses `workers_to_read_batch` so the clash cache is consulted once for the whole set
- `batch_delete_workers` requires `entity_manage_any` (coordinator+), checks data lock on every worker before deleting any, and decrements permit counts for permit-linked workers
- Work group association validated via `alert_service.py::validate_work_group_association`
- Worker copies force `locked=False` and inject `created_by_contractor` audit metadata
- `_build_entity` requires a position; 400 if none resolved
- `model_fields_set` distinguishes "not sent" from "sent as null" for `building_level`, `building_feature_id`, and `work_group_id`

## Touches
| resource | how | why |
|---|---|---|
| services/backend/modules/entity_service.md | Extends `EntityServiceBase` | Shared CRUD, OCC, tombstone lifecycle |
| services/backend/modules/entity_schedule.md | Delegates schedule group ops | Recurring schedule lifecycle |
| services/backend/modules/entity_broadcast_audit.md | `_invalidate_and_broadcast`, `_audit.record` | WS events + audit trail |
| services/backend/modules/core_rbac.md | `require_site_permission`, `get_entity_visibility_filter` | RBAC + contractor scoping |
| services/backend/modules/data_lock.md | `_check_data_lock` | Blocks edits inside locked periods |
| services/backend/modules/clash_proximity.md | `worker_to_read`, `workers_to_read_batch`, `workers_to_read_lite` | Colour state + batch serialization |
| services/backend/modules/planning_cycle.md | `CycleService.resolve_cycle_tag_for_create` | Tags new workers with cycle + plan_state |
| services/backend/modules/permit_import.md | `extract_permit_link`, `decrement_permit_counts_for_deleted_entities` | Permit count sync on batch delete |

## Gotchas
- `list_workers` returns colour state as "green"; actual severity is derived on the frontend from the live clash list
- `batch_delete_workers` checks data lock for every matched worker before deleting any; if one is locked, the entire batch fails
- Pixel-coordinate resolution requires `site_map.metres_per_pixel`; 400 if the map is uncalibrated
- `_apply_shared_updates` does not validate work group association; shared updates bypass `alert_service` validation
