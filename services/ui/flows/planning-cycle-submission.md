---
trigger: { channel: ui, ref: "planning panel submit action" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User interacts with the planning panel to create, submit, review, actualize, archive, import, or carry-forward a planning cycle.

## Steps

### Cycle creation
1. `dashboard/planning-panel/planning-cycle-create-form.component.ts::PlanningCycleCreateFormComponent` renders the new-cycle form (start, end, label, adopt-existing checkbox).
2. `dashboard/planning-panel/planning-panel.store.ts::PlanningPanelStore.createCycle` converts datetime-local inputs to ISO-UTC via `datetimeLocalToIso`.
3. `services/planning-cycle.service.ts::PlanningCycleService.createCycle` → `PlanningApi.createCycle()` POST to backend.
4. Backend creates the cycle; if `adopt_existing=true`, intersecting baseline entities are re-tagged as planned.
5. On success, `PlanningPanelStore` clears form fields and calls `PlanningCycleService.refreshCycles`.

### App mode and active cycle
6. `services/planning-cycle.service.ts::PlanningCycleService.activeCycle$` emits the cycle overlapping `siteContext.selectedDate$` using lexicographic ISO overlap (`cycleOverlapsCalendarDate`).
7. Default `appMode` auto-applies via `activeCycle$` subscription: `editing_plan` for `planning` status, `editing_actual` otherwise, unless `_userOverrodeMode` is true.
8. `services/planning-view-mode.service.ts::PlanningViewModeService.viewMode$` derives the legacy 3-value label (`editing` | `review_submitted` | `comparing`) from `appMode$`.

### Entity creation scope
9. `services/planning-cycle.service.ts::PlanningCycleService.getCycleIdForCreation$` returns the active cycle id for planned entities.
10. Returns `undefined` in `editing_actual` with a draft (`planning`) cycle active → forces baseline creation outside plan scope.
11. `services/schedule-orchestration.service.ts::ScheduleOrchestrationService` consumes this in all batch schedule creation paths (`confirmScheduleCreation`, `createPlantScheduleFromModal`, `createWorkerScheduleFromModal`, `createAreaScheduleFromModal`).

### Submission workflow
12. Contractor (or coordinator with `coordinatorCanSubmitPlans`) clicks Submit on a row in `dashboard/planning-panel/planning-cycle-card.component.ts::PlanningCycleCardComponent`.
13. `dashboard/planning-panel/planning-panel.store.ts::PlanningPanelStore.submitPlan` → `services/planning-cycle.service.ts::PlanningCycleService.submitPlan` → `PlanningApi.submitPlan()`.
14. Coordinator reviews: `PlanningPanelStore.loadSubmissionInsights` fetches batched `SubmissionInsight` counts; `loadSubmissionInsightDetail` expands per-contractor row lists.
15. Coordinator approves: `PlanningPanelStore.approveSubmission` → `PlanningCycleService.approveSubmission` → POST approve.
16. Coordinator requests revision: `PlanningPanelStore.sendRevision` → `PlanningCycleService.requestRevision` → POST with optional note.
17. Bulk actions: `approveAllSubmitted` and `submitAllPending` iterate the full submission list in one backend call each.

### Pending badge refresh
18. `PlanningPanelStore` merges `entityService.tokens$`, `plants$`, `areas$`, and `deliveryService.deliveries$`, pipes through `auditTime(300)`, and calls `refreshPendingSummaryForSelectedCycle`.
19. `loadAllPendingSummaries` fetches batched `PendingSummary` for every contractor in one request.

### Compare mode and clash diff
20. User selects Compare (overlay) or Split from the app-mode dropdown.
21. `services/planning-cycle.service.ts::PlanningCycleService.compareData$` (overlay) and `splitCompareData$` (split) fetch `PlanningApi.compare()` for the active cycle.
22. Results are cached by cycle id in `_compareDataCache`; cache is cleared on site changes, cycle transitions, and entity mutations.
23. `clashDiff$` fetches `PlanningApi.clashDiff()` on demand and caches by cycle id in `_clashDiffCache`.

### Actualize
24. Coordinator clicks Go Live on a `planning` cycle in `PlanningCycleCardComponent`.
25. `PlanningPanelStore.prepareActualize` loads `submissionSummary` to show counts of approved/draft/submitted/revision-requested rows.
26. `confirmActualize` → `PlanningCycleService.actualize` → POST actualize.
27. Backend forks planned rows to actual state, deletes tombstoned rows, and sets cycle status to `live`.
28. `planning_actualized` WebSocket event triggers `refreshCycles` and `forceRefreshEntities`.

### Archive
29. Coordinator clicks Archive Cycle on a `live` cycle.
30. `PlanningPanelStore.confirmClose` → `PlanningCycleService.updateStatus` with `'archived'`.
31. Transitions are irreversible: `planning` → `live` → `archived` only.

### Baseline import
32. Coordinator clicks Import Current Entities on a `planning` cycle.
33. `PlanningPanelStore.importBaseline` → `PlanningCycleService.importBaseline` → POST import.
34. Backend pulls non-cycle baseline entities into the cycle as planned rows.

### Carry forward
35. Coordinator clicks Carry Forward to... on a `live` or `archived` cycle.
36. `PlanningPanelStore.carryForward` → `PlanningCycleService.carryForward` with source and target cycle ids.
37. Backend copies entities to the target planning cycle, date-shifting by the offset between cycle starts.

### Review submitted (plan preview)
38. User clicks Review Submitted on a cycle.
39. `PlanningPanelStore.toggleReviewSubmission` → `PlanningCycleService.reviewSubmission` sets `appMode` to `viewing_submitted` with a `PlanPreviewTarget`.
40. `planPreviewData$` loads compare data for that cycle id and contractor filter.

## Side effects
- HTTP writes: create cycle, submit/approve/revision, actualize, archive, import baseline, carry forward, compare, clash diff, submission insights.
- WebSocket emits to `site:{site_id}` room: `planning_cycle_updated`, `planning_actualized`, `planning_carry_forward`, `planning_baseline_imported`, `planning_submission_updated`, `planning_submissions_bulk_updated`.
- State mutations: `_cycles`, `_appMode`, `_submissions`, `_compareDataCache`, `_clashDiffCache`, `_planPreviewTarget`, `planning-panel.store.ts::PlanningPanelStore` signals (cycles, submissions, submissionRows, pendingSummaryMap).
- Entity cache invalidation: `DataLoadService.forceRefreshEntities` called on actualize, carry-forward, baseline-import, and submission-update events.
- Compare cache invalidation: `_clearCompareCaches` on site change, cycle transition, entity mutation WS events, and submission updates.

## Failure modes
- **Overlapping cycle window**: detected by `PlanningPanelStore.newCycleDateError` (client-side overlap check); blocks Create button.
- **Create API failure**: caught in `createCycle` subscribe error path; toast shown via `MessageService`.
- **Submit without permission**: UI hides Submit button unless `userService.isMember()` with matching contractor id or `isCoordinatorOrAbove && coordinatorCanSubmitPlans`.
- **Actualize with unapproved submissions**: `hasUnapprovedSubmissions` computed flag warns in the confirmation panel; backend will still proceed.
- **Actualize empty cycle**: backend returns 422; displayed via `extractApiErrorMessage` toast.
- **Compare fetch failure**: `_compareError` set to true; toast shown; retry available via `retryCompare`.
- **Entity jump-to timeout**: `_resolveLiveThen` times out at 3s if the entity is not in the live cache after time-jump; warns "no longer on the map".
- **Pre-migration audit entries**: cannot be reverted from the UI (backend invariant).
