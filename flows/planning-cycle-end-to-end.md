---
trigger: { channel: ui, ref: "planning panel action" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User creates, submits, or manages a planning cycle from the planning panel.

## Steps

### Cycle creation
1. `PlanningCycleCreateFormComponent` renders the new-cycle form (start, end, label, adopt-existing checkbox).
2. `PlanningPanelStore.createCycle` converts datetime-local inputs to ISO-UTC via `datetimeLocalToIso`.
3. `PlanningApi.createCycle()` POST to backend.
4. Backend `planning_cycle_service.py::create_cycle` validates window overlap, inserts `PlanningCycle` row.
5. If `adopt_existing=true`, `import_on_cycle_open` re-tags intersecting baseline entities as `plan_state='planned'`.
6. On success, frontend clears form fields and calls `refreshCycles`.

### Entity scope
7. `PlanningCycleService.getCycleIdForCreation$` returns the active cycle id for planned entities.
8. Returns `undefined` in `editing_actual` with a draft (`planning`) cycle active → forces baseline creation outside plan scope.

### Baseline import
9. Coordinator clicks Import Current Entities on a `planning` cycle.
10. `PlanningPanelStore.importBaseline` → `PlanningApi.importBaseline()` POST.
11. Backend `import_baseline_service.py::import_baseline` shadows baseline rows into the cycle.
12. Re-import is not idempotent on cycles with native modifications.

### Submission
13. Contractor clicks Submit; `PlanningPanelStore.submitPlan` → `PlanningApi.submitPlan()` POST.
14. Backend `submission_service.py::submit_plan` calls `SubmissionSnapshotService.sync_contractor_plan`.
15. `sync_contractor_plan` acquires advisory lock, deletes prior snapshot items, inserts fresh `ContractorSubmissionSnapshotItem` rows.
16. Coordinator approves: `PlanningPanelStore.approveSubmission` → POST approve.
17. Backend `SubmissionService.approve_submission` transitions status to `approved`.
18. Bulk actions: `approveAllSubmitted` and `submitAllPending` iterate the full list in one backend call.

### Actualize
19. Coordinator clicks Go Live on a `planning` cycle.
20. `PlanningPanelStore.confirmActualize` → `PlanningApi.actualize()` POST.
21. Backend `actualize_service.py::actualize` forks planned rows to `actual`, deletes tombstoned rows, sets cycle status to `live`.
22. `ws_manager.broadcast_to_room` emits `planning_actualized` to `site:{site_id}`.
23. `entity_broadcast.py::invalidate_clash_cache` triggers recomputation.

### WebSocket handling
24. Frontend receives `planning_cycle_updated`, `planning_actualized`, `planning_carry_forward`, `planning_baseline_imported`, `planning_submission_updated`.
25. Events trigger `refreshCycles`, `_clearCompareCaches`, and `DataLoadService.forceRefreshEntities`.

### Archive and carry forward
26. Coordinator clicks Archive Cycle on a `live` cycle.
27. `PlanningPanelStore.confirmClose` → `PlanningCycleService.updateStatus` with `'archived'`.
28. Backend `CycleService.transition_status` enforces irreversible `planning` → `live` → `archived` only.
29. Coordinator clicks Carry Forward; backend copies entities to target cycle, date-shifting by offset between cycle starts.

## Side effects
- PostGIS INSERT/UPDATE/DELETE of entity rows and `PlanningCycle` status
- Audit trail entries for every state change
- WebSocket events to `site:{site_id}` room
- Redis pub/sub relay for cross-process broadcast
- Debounced clash cache recomputation
- Frontend state mutations: `_cycles`, `_appMode`, `_submissions`, `_compareDataCache`, `_clashDiffCache`

## Failure modes
- **Overlapping cycle window**: client-side `newCycleDateError` blocks Create; backend returns 409 Conflict.
- **Actualize empty cycle**: backend `any_planned_rows` check returns 422.
- **Actualize non-planning cycle**: backend status guard returns 422.
- **Invalid status transition**: backend `_VALID_TRANSITIONS` check returns 422.
- **Submit without permission**: UI hides Submit button unless user is member with matching contractor id or coordinator with `coordinatorCanSubmitPlans`.
- **Actualize with unapproved submissions**: `hasUnapprovedSubmissions` warns in confirmation panel; backend still proceeds.
- **Pre-migration audit entries**: cannot be reverted from the UI (backend invariant).
- **Concurrent import/actualize**: `pg_advisory_xact_lock` serialises by PostgreSQL advisory lock.
- **Compare fetch failure**: `_compareError` set to true; retry available via `retryCompare`.

## Cross-references
- [frontend journey](../services/ui/flows/planning-cycle-submission.md)
- [backend cycle lifecycle](../services/backend/flows/planning_cycle_lifecycle.md)
- [backend submission flow](../services/backend/flows/planning_submission_flow.md)
