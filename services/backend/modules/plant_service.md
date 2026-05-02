---
service: backend
summary: "Plant CRUD with inactive crane synthesis and schedule operations"
paths:
  - backend/app/services/entity/plant_service.py
flows:
  - services/backend/flows/entity_creation.md
  - services/backend/flows/entity_update.md
touches:
  - services/backend/modules/entity_service.md
  - services/backend/modules/entity_schedule.md
  - services/backend/modules/entity_broadcast_audit.md
  - services/backend/modules/core_rbac.md
  - services/backend/modules/data_lock.md
  - services/backend/modules/planning_cycle.md
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Orchestrates plant CRUD via `EntityServiceBase`. Synthesises inactive crane
representations from historical placements so physical obstacles persist between
active shifts. Supports schedule groups, position-group deletion, and range copy.

## Interface
- `plant_service.py::synthesize_inactive_cranes_from_plants(cranes, query_start, query_end)` → list[PlantRead]
- `plant_service.py::PlantService.create_plant(user, payload)` → PlantRead
- `plant_service.py::PlantService.update_plant(user, plant_id, payload)` → PlantRead
- `plant_service.py::PlantService.delete_plant(user, plant_id)` → None
- `plant_service.py::PlantService.restore_plant(user, plant_id)` → PlantRead
- `plant_service.py::PlantService.list_plants(user, site_id, query_start, query_end)` → list[PlantRead]
- `plant_service.py::PlantService.get_plant(user, plant_id)` → PlantRead
- `plant_service.py::PlantService.copy_plants_from_range(user, payload)` → PlantCopyResponse
- `plant_service.py::PlantService.create_plant_schedule(user, payload)` → ScheduleCreateResponse
- `plant_service.py::PlantService.delete_plant_schedule_group(user, group_id)` → None
- `plant_service.py::PlantService.get_plant_schedule_group(user, group_id)` → list[PlantRead]
- `plant_service.py::PlantService.update_plant_schedule_group(user, group_id, payload)` → list[PlantRead]
- `plant_service.py::PlantService.reconcile_plant_schedule_group(user, group_id, request)` → ScheduleReconcileResponse
- `plant_service.py::PlantService.convert_plant_to_schedule(user, plant_id, request)` → ScheduleCreateResponse
- `plant_service.py::PlantService.delete_plant_position_group(user, source_plant_id)` → int

## State
None at module level. All state is persistent (PostGIS).

## Internals
- `synthesize_inactive_cranes_from_plants` is pure (no DB access) so both live list and audit-reconstructed `/api/plant/at-time` paths share the same reduction rules
- Grouping key is `schedule_group_id` when present, otherwise rounded WGS84 coordinates (`pos:{round(x)}:{round(y)}`)
- Synthetic inactive spans from earliest `start_at` to latest `end_at` (open-ended if any occurrence lacks an end)
- `list_plants` queries active plants via `apply_temporal_filter`, then appends inactive cranes placed before `query_end`
- `delete_plant_position_group` deletes all cranes/concrete pumps at the same rounded position — used when removing an inactive representation
- `_resolve_position` accepts `position_wgs84` (→ EPSG:3857 WKB) or `position_m` (→ SRID 3857 directly)
- `_build_entity` auto-assigns `contractor_id` from membership when the caller is a contractor member
- Work group association validated via `alert_service.py::validate_work_group_association`
- Plant copies force `locked=True` and preserve source `extra` verbatim (no audit metadata)
- `include_shadowed_baselines=True` keeps import-shadowed baseline rows visible for `editing_actual` mode

## Touches
| resource | how | why |
|---|---|---|
| services/backend/modules/entity_service.md | Extends `EntityServiceBase` | Shared CRUD, OCC, tombstone lifecycle |
| services/backend/modules/entity_schedule.md | Delegates schedule group ops | Recurring schedule lifecycle |
| services/backend/modules/entity_broadcast_audit.md | `_invalidate_and_broadcast`, `_audit.record` | WS events + audit trail |
| services/backend/modules/core_rbac.md | `require_site_permission`, `get_entity_visibility_filter` | RBAC + contractor scoping |
| services/backend/modules/data_lock.md | `_check_data_lock` | Blocks edits inside locked periods |
| services/backend/modules/planning_cycle.md | `CycleService.resolve_cycle_tag_for_create` | Tags new plants with cycle + plan_state |
| services/backend/modules/clash_proximity.md | `plant_to_read`, `plant_to_inactive_read` | Drop-zone geometry for clash detection |

## Gotchas
- Inactive cranes without `base_position` or `start_at` are dropped silently; live SQL filters them, but the at-time path may include them
- `delete_plant_position_group` uses rounded-coordinate matching; two cranes at `(1.4, 2.6)` and `(1.6, 2.4)` round to the same group and would both be deleted
- `_apply_shared_updates` does not validate work group association; shared updates bypass `alert_service` validation
- `model_fields_set` is used to distinguish "not sent" from "sent as null" for `building_level`, `building_feature_id`, and `work_group_id`
