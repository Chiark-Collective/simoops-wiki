---
service: backend
summary: "Compare, carry-forward, actualize, and import-baseline helpers"
paths: [
  backend/app/services/planning/compare_service.py,
  backend/app/services/planning/clash_compare_service.py,
  backend/app/services/planning/pending_row_differ.py,
  backend/app/services/planning/carry_forward_service.py,
  backend/app/services/planning/actualize_service.py,
  backend/app/services/planning/cycle_open_import.py,
  backend/app/services/planning/window.py,
  backend/app/services/planning/snapshot_reconstruction.py,
  backend/app/services/planning/snapshot_coercion.py,
  backend/app/services/planning/entity_copy.py,
  backend/app/services/planning/cycle_entity_loader.py,
]
flows: [planning_cycle_lifecycle]
touches: [postgis]
external: []
last_verified_commit: TBD
---

## Purpose

Provides divergence detection between planned and actual states, clash diffing,
and utilities for moving entities between cycles (carry-forward, import,
actualize).

## Interface

- `CompareService(session).compare(cycle_id)` → `CompareResponse` (snapshot vs current row)
- `ClashCompareService(session).compute_clash_diff(cycle_id)` → `ClashDiffResult`
- `CarryForwardService(session).carry_forward(source_cycle_id, target_cycle_id, ...)` → `CarryForwardResult`
- `ActualizeService(session).actualize(cycle_id, user_id)` → `ActualizeResult`
- `ImportBaselineService(session).import_baseline(cycle_id, ...)` → `ImportBaselineResult`
- `backend/app/services/planning/pending_row_differ.py::pending_rows_for_cycle(session, cycle)` → `PendingContractorRows`
- `backend/app/services/planning/pending_row_differ.py::pending_rows_for_contractor(session, cycle, contractor_id)` → `PendingContractorRows`
- `backend/app/services/planning/cycle_entity_loader.py::load_cycle_entities(session, model, ...)` → cycle-tagged baseline rows
- `backend/app/services/planning/cycle_entity_loader.py::load_cycle_snapshot_items(session, cycle_id, entity_type)` → raw snapshot dicts
- `backend/app/services/planning/cycle_entity_loader.py::load_cycle_snapshot_rows(session, ...)` → hydrated duck-typed dataclasses
- `backend/app/services/planning/snapshot_reconstruction.py::load_planned_entities_from_snapshots(session, cycle_id, site_id)` → reconstructed tokens/plants/features
- `backend/app/services/planning/entity_copy.py::copy_entity_columns(source, model_class)` → dict for forked row creation

## State

`ClashCompareService` maintains a module-level cache:

| State | Location | Lifecycle |
|---|---|---|
| `_clash_diff_cache` | `dict[UUID, (ClashDiffResult, str, float)]` | In-memory; 60s TTL + `max(updated_at)` key |

### Invariants

- Cache key = `max(entity.updated_at)` across cycle entities
- `_CACHE_TTL_SECONDS = 60` ⟂ stale reads within TTL window
- Empty cache on process restart

## Internals

- `CompareService` diffs current rows against `ContractorSubmissionSnapshotItem` records by entity id (SP2(a))
- `_diff_snapshot_vs_row` uses shapely `equals` for geometry comparison to avoid WKB/GeoJSON roundtrip noise
- `ClashCompareService` evaluates planned clashes from submission snapshots (not `plan_state='planned'` rows, which don't exist post-actualize)
- `ClashCompareService._build_inputs_for_state` uses `snapshot_reconstruction.py` for planned side, live DB queries for actual side
- `pending_row_differ.py` identifies rows authored since last submission by id absence from snapshot + `created_at`/`updated_at` recency
- `carry_forward_service.py` copies actual rows as planned with datetime offset; features copied first so token `zone_id` remapping resolves
- `cycle_entity_loader.py` unifies baseline + snapshot loaders previously scattered across services
- `snapshot_coercion.py` parses GeoJSON, UUIDs, datetimes, enums; lifts `building_level`/`building_feature_id` from legacy `extra` blobs
- `window.py::overlap_clauses` handles null semantics: `start=NULL` → unbounded left; `end=NULL` + start set → point-in-time

## Touches

| resource | how | why |
|---|---|---|
| postgis | SQLModel select | Baseline rows, snapshots, clash inputs |
| [clash_engine](clash_engine.md) | `_compute_clashes_sync` | Evaluate planned vs actual clashes |
| [websocket_runtime](websocket_runtime.md) | `ws_manager.broadcast_to_room` | Import/actualize/carry-forward events |

## Gotchas

- `CompareService` returns `pending_rows` only for `planning`-status cycles
- `ClashCompareService` requires `live` or `archived` cycles
- Carry-forward `zone_id` remap fails silently if the referenced feature wasn't carried (defensive `id_remap.get`)
- Pre-086 snapshots nest `building_level` in `extra`; `lift_legacy_extra_keys` must stay in sync with schema
