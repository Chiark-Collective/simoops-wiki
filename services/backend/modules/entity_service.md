---
service: backend
summary: "Abstract base and helpers for entity CRUD, copy, and schedule lifecycle"
paths:
  - backend/app/services/entity/entity_service.py
  - backend/app/services/entity/entity_copy_helpers.py
  - backend/app/services/entity/snapshot_reconstructors.py
  - backend/app/services/entity/area_copy_service.py
flows:
  - services/backend/flows/entity_creation.md
  - services/backend/flows/entity_update.md
touches: []
external: []
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose
Provides `EntityServiceBase`, an abstract generic class that defines the shared
lifecycle for worker, plant, and similar entity CRUD. Subclasses implement
entity-specific construction, serialization, and field-update hooks. Copy and
schedule helpers are parameterised so the same orchestration works across types.

## Interface
- `entity_service.py::EntityServiceBase` — abstract generic base for entity CRUD
- `entity_service.py::EntityServiceBase.create_entity(user, payload)` → TRead
- `entity_service.py::EntityServiceBase.update_entity(user, entity_id, payload)` → TRead
- `entity_service.py::EntityServiceBase.delete_entity(user, entity_id)` → None
- `entity_service.py::EntityServiceBase.restore_entity(user, entity_id)` → TModel
- `entity_service.py::EntityServiceBase.delete_schedule_group(user, group_id)` → None
- `entity_service.py::EntityServiceBase.get_schedule_group(user, group_id)` → list[TRead]
- `entity_service.py::EntityServiceBase.update_schedule_group(user, group_id, payload)` → list[TRead]
- `entity_service.py::EntityServiceBase.reconcile_schedule_group(user, group_id, request)` → ScheduleReconcileResponse
- `entity_service.py::EntityServiceBase.convert_to_schedule(user, entity_id, request)` → ScheduleCreateResponse
- `entity_service.py::EntityServiceBase._check_optimistic_concurrency(entity, payload, site)` → None
- `entity_copy_helpers.py::copy_entities_from_range(...)` → ResponseT
- `entity_copy_helpers.py::create_entity_schedule(...)` → response_class
- `snapshot_reconstructors.py::reconstruct_delivery(snap)` → Delivery | None
- `snapshot_reconstructors.py::reconstruct_poi(snap)` → PointOfInterest | None
- `snapshot_reconstructors.py::reconstruct_text_label(snap)` → TextLabel | None
- `snapshot_reconstructors.py::worker_audit_row_to_read(audit_row, site_id)` → WorkerRead | None
- `snapshot_reconstructors.py::plant_audit_row_to_read(audit_row, site_id)` → PlantRead | None
- `area_copy_service.py::AreaCopyService.copy_areas_from_range(user, payload)` → AreaCopyResponse

## Internals
- `_require_contractor_access` called during `create_entity` (was only on update/delete); members may only create entities tagged with their own `contractor_id`
- Abstract hooks: `_build_entity`, `_apply_updates`, `_entity_to_read`, `_clone_entity_for_schedule`, `_get_field_groups`
- `_check_optimistic_concurrency` implements field-level OCC using `expected_updated_at` and `last_modified_fields`
- `_get_field_groups` maps raw DB fields to semantic groups (e.g. `position_m` + `position_wgs84` → `position`)
- `delete_entity` hard-deletes baseline/actual rows; soft-deletes (`tombstoned_at`) planned rows
- `restore_entity` reverses a tombstone and re-broadcasts as `entity_created`
- `copy_entities_from_range` rejects identical source/target ranges and copies with temporal offset
- `create_entity_schedule` resolves occurrences against site shifts or custom times
- `snapshot_reconstructors` re-injects `id`/`site_id` stripped by `DIFF_EXCLUDED_FIELDS` before reconstruction
- `area_copy_service` deduplicates by `(name, feature_type)` and creates `FeatureVersion` records per copy

## Touches
| resource | how | why |
|---|---|---|
| services/backend/modules/core_rbac.md | `require_site_permission` / `get_entity_visibility_filter` | RBAC checks for every mutation |
| services/backend/modules/data_lock.md | `require_not_locked` via `_check_data_lock` | Blocks edits inside locked periods |
| services/backend/modules/entity_broadcast_audit.md | `broadcast_entity_event`, `invalidate_and_broadcast` | Broadcast + clash invalidation |
| services/backend/modules/entity_schedule.md | Delegates schedule group ops | Schedule lifecycle |

## Gotchas
- `EntityServiceBase` never calls `commit()` inside broadcast helpers; commit happens in the CRUD method so audit + entity writes are atomic
- `_check_data_lock` uses `entity_end_at`, not payload end_at, for updates — an entity whose end_at is in the locked past cannot be edited even if the payload would move it forward
- `last_modified_fields` is cleared during `update_schedule_group` because shared updates bypass `update_entity`; next OCC check falls back to whole-entity 409
- Planned-row tombstones are broadcast as `entity_deleted` so clients hide them immediately; restore re-broadcasts as `entity_created`
- Area copy does NOT copy `schedule_group_id`; copied areas are standalone
