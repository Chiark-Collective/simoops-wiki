---
service: backend
summary: "Planning cycle lifecycle: draft, import-baseline, actualize, archive"
paths: [
  backend/app/services/planning/cycle_service.py,
  backend/app/services/planning/import_baseline_service.py,
  backend/app/services/planning/cycle_open_import.py,
  backend/app/services/planning/actualize_service.py,
  backend/app/services/planning/carry_forward_service.py,
  backend/app/services/planning/window.py,
  backend/app/services/planning/entity_copy.py,
]
flows: [entity_creation, planning_cycle_lifecycle, planning_submission_flow]
touches: [postgis]
external: []
last_verified_commit: TBD
---

## Purpose

Manages the lifecycle of a site's plan through draft → live → archived states.
Supports what-if analysis via planned-row sandboxes that do not propagate to
baselines until actualized.

## Interface

- `CycleService(session)` → CRUD and status transitions
- `CycleService.create_cycle(site_id, start_at, end_at, ...)` → new planning cycle
- `CycleService.create_cycle_with_submissions(site_id, ...)` → cycle + contractor submissions
- `CycleService.transition_status(cycle_id, target_status, user_id)` → archived only
- `CycleService.plan_state_for_new_entity(cycle)` → `PlanState.planned` or `actual`
- `CycleService.resolve_cycle_tag_for_create(...)` → `(planning_cycle_id, plan_state)` pair
- `ImportBaselineService(session).import_baseline(cycle_id, ...)` → re-tag baseline rows into cycle
- `ActualizeService(session).actualize(cycle_id, user_id)` → flip planned rows to actual in place
- `CarryForwardService(session).carry_forward(source_cycle_id, target_cycle_id, ...)` → copy actuals as planned

## State

Runtime state is minimal; primary state is in DB.

| State | Location | Lifecycle |
|---|---|---|
| PlanningCycle row | postgis | Persistent |
| planned rows (`plan_state='planned'`) | postgis | Persistent; tombstoned on removal |

### Invariants

- `planned` row origin asymmetry:
  - NATIVE: `source_row_id` IS NULL (placed directly in cycle)
  - SHADOW: `source_row_id` points at baseline (imported via `import-baseline`)
- Native rows have no baseline counterpart; shadow rows hide their baseline via `apply_plan_state_filter`
- Actualize flips planned → actual; baseline mutations do NOT propagate into cycle mid-flight
- Cycles on the same site must not overlap

## Internals

- `_VALID_TRANSITIONS` permits only `live → archived`
- Entering live mode requires `ActualizeService`, not generic transition endpoint
- `import_on_cycle_open` auto-imports baseline when cycle opens (`adopt_existing=True`)
- `apply_plan_state_filter` hides baselines with shadow counterparts from non-cycle queries
- Advisory locks via `backend/app/services/planning/entity_copy.py::advisory_lock_key` prevent concurrent actualize/import/carry-forward
- `backend/app/services/planning/window.py::window_bounds` and `overlap_clauses` define half-open cycle windows
- Post-actualize clash cache invalidation triggers [clash_engine](clash_engine.md) recomputation
- Status transitions broadcast via [websocket_runtime](websocket_runtime.md) using [redis_core](redis_core.md) pub/sub relay

## Touches

| resource | how | why |
|---|---|---|
| postgis | SQLModel CRUD | Persistent cycle and entity state |
| [websocket_runtime](websocket_runtime.md) | `ws_manager.broadcast_to_room` | Real-time cycle status updates |
| [redis_core](redis_core.md) | Pub/sub relay | Cross-process broadcast of cycle events |
| [clash_engine](clash_engine.md) | `invalidate_clash_cache` | Recompute clashes after actualize |

## Gotchas

- Some transitions are irreversible (live → archived). No rollback path.
- Re-running `import-baseline` must be idempotent.
- Entity modifications in live cycles may still be subject to [data_lock](data_lock.md) boundaries.
- Route-layer access to cycle endpoints is gated by [core_rbac](core_rbac.md) site permissions.
- See [gotchas.md](../../../gotchas.md) for full footgun list.
