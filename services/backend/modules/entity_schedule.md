---
service: backend
summary: "Temporal scheduling for entities: shifts, occurrences, reconcile, convert"
paths:
  - backend/app/services/entity/entity_schedule_service.py
  - backend/app/services/entity/area_schedule_service.py
  - backend/app/services/entity/schedule_ops.py
  - backend/app/services/entity/schedule_reconcile.py
  - backend/app/services/entity/schedule_time.py
flows: []
touches: []
external: []
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Standalone schedule operations for entity types (worker, plant, area). Resolves
occurrence times against site shifts, reconciles planned vs actual occurrences,
and converts standalone entities into recurring schedules.

## Interface
- `entity_schedule_service.py::delete_schedule_group(session, user, group_id, model_class, ...)` → None
- `entity_schedule_service.py::get_schedule_group(session, user, group_id, model_class, entity_to_read)` → list
- `entity_schedule_service.py::update_schedule_group(session, user, group_id, payload, model_class, ...)` → list
- `entity_schedule_service.py::reconcile_schedule_group(session, user, group_id, request, model_class, ...)` → ScheduleReconcileResponse
- `entity_schedule_service.py::convert_to_schedule(session, user, entity_id, request, model_class, ...)` → ScheduleCreateResponse
- `area_schedule_service.py::AreaScheduleService.convert_area_to_schedule(user, feature_id, request)` → ScheduleCreateResponse
- `area_schedule_service.py::AreaScheduleService.create_area_schedule(user, payload)` → ScheduleCreateResponse
- `area_schedule_service.py::AreaScheduleService.get_area_schedule_group(user, group_id)` → list[GeometadataFeatureRead]
- `area_schedule_service.py::AreaScheduleService.update_area_schedule_group(user, group_id, payload)` → list[GeometadataFeatureRead]
- `area_schedule_service.py::AreaScheduleService.delete_area_schedule_group(user, group_id)` → None
- `area_schedule_service.py::AreaScheduleService.reconcile_area_schedule_group(user, group_id, request)` → ScheduleReconcileResponse
- `schedule_ops.py::load_site_shifts(session, site_id)` → list[Shift]
- `schedule_ops.py::set_occurrence_count(items, total_count, dict_attr)` → None
- `schedule_ops.py::merge_extra_dict(entity, updates, dict_attr)` → None
- `schedule_reconcile.py::resolve_occurrences(request, shifts)` → list[tuple[datetime, datetime]]
- `schedule_reconcile.py::match_occurrences(existing_items, new_times, get_times)` → tuple[list[T], list, list[T]]
- `schedule_reconcile.py::match_original_against_occurrences(original_start, original_end, resolved_times)` → tuple[int | None, list]
- `schedule_time.py::resolve_occurrence_times(date_str, shift)` → tuple[datetime, datetime]
- `schedule_time.py::resolve_custom_times(date_str, start_time_str, end_time_str)` → tuple[datetime, datetime]

## Internals
- `load_site_shifts` orders by `(created_at, id)` to match the list endpoint so `shift_index` is stable
- `resolve_occurrence_times` handles overnight shifts by adding a day when `end_at <= start_at`
- `resolve_custom_times` validates `HH:MM` format and applies the same overnight rule
- `match_occurrences` normalises times to minute precision (tz stripped) for reliable matching
- `reconcile_schedule_group` matches existing entities by `(start_at, end_at)`; creates siblings for unmatched occurrences; deletes unmatched existing
- `convert_to_schedule` assigns a new `schedule_group_id` to the original entity and clones siblings
- Area schedule ops create `FeatureVersion` records for every mutation (`create`, `update`, `delete`)
- `set_occurrence_count` writes `schedule_occurrence_count` into `extra` (tokens/plants) or `properties` (areas)
- Area shared updates use `model_fields_set` to distinguish "not sent" from "sent as null" for building placement fields

## Touches
| resource | how | why |
|---|---|---|
| services/backend/modules/entity_service.md | Delegated from `EntityServiceBase` | Schedule group lifecycle |
| services/backend/modules/entity_broadcast_audit.md | `broadcast_entity_event`, `invalidate_and_broadcast` | WS events + audit on schedule changes |

## Gotchas
- `update_schedule_group` clears `last_modified_fields` on every entity; the next OCC check falls back to whole-entity 409
- `match_occurrences` uses a dict keyed by normalised `(start, end)`; if two existing entities share identical times, one is overwritten and may be incorrectly deleted
- `convert_to_schedule` requires `entity_edit` permission; members can only convert their own contractor's entities
- Area schedule create auto-sets `clashable` from `CLASHABLE_FEATURE_TYPES` when not explicitly provided
- `reconcile_schedule_group` checks data lock on all existing entities before mutation, and on all new occurrences before creation
