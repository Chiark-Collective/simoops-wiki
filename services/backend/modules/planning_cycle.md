---
service: backend
summary: "Planning cycle lifecycle: draft, import-baseline, actualize, archive"
paths: [backend/app/services/planning/cycle_service.py, backend/app/services/planning/actualize_service.py, backend/app/services/planning/import_baseline_service.py]
flows: [entity_creation]
touches: [postgis]
external: []
last_verified_commit: TBD
---

# Planning Cycle

## Purpose

Manages the lifecycle of a site's plan through draft → live → archived states. Supports what-if analysis via planned-row sandboxes that do not propagate to baselines until actualized.

## Interface

- `CycleService(session)` → CRUD and status transitions
- `CycleService.create(site_id, ...)` → new planning cycle
- `CycleService.transition(cycle_id, status)` → archived (only valid transition)
- `ImportBaselineService.import_baseline(cycle_id)` → shadow baseline rows into cycle
- `ActualizeService.actualize(cycle_id)` → fork planned rows to actual baseline
- `SubmissionService.submit(cycle_id)` → submit for review

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
- Actualize forks planned → actual; baseline mutations do NOT propagate into cycle mid-flight

## Internals

- `_VALID_TRANSITIONS` permits only `live → archived`
- Entering live mode requires `ActualizeService`, not generic transition endpoint
- `import_on_cycle_open` auto-imports baseline when cycle opens
- `apply_plan_state_filter` hides baselines with shadow counterparts from non-cycle queries

## Touchas

| Resource | How | Why |
|---|---|---|
| postgis | SQLModel CRUD | Persistent cycle and entity state |

## Gotchas

- Some transitions are irreversible (active → archived). No rollback path.
- Re-running `import-baseline` must be idempotent.
- See [gotchas.md](../../../gotchas.md) for full footgun list.
