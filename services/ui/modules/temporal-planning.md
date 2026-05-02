---
service: ui
summary: Shift, date, scrubber context and planning cycle orchestration.
paths:
  - services/temporal-context.service.ts
  - services/planning-cycle.service.ts
  - services/planning-view-mode.service.ts
  - services/revision-mode.service.ts
  - services/revision-timeline.service.ts
  - services/gantt-computation.service.ts
  - services/schedule-orchestration.service.ts
  - services/time-utility.service.ts
  - services/timezone.service.ts
  - services/sun-times.service.ts
  - services/timeline-operations.service.ts
  - services/time-mode-resolver.ts
  - timeline/timeline.component.ts
  - dashboard/timeline-bar/
  - dashboard/timeline-dock/
  - dashboard/planning-panel/
  - types/planning.types.ts
  - types/gantt.types.ts
  - types/schedule.types.ts
flows:
  - temporal-context.service.ts::TemporalContextService.context$ → entity load fetch specs
  - planning-cycle.service.ts::PlanningCycleService.activeCycle$ → view mode default
  - revision-timeline.service.ts::RevisionTimelineService.load → revision-mode.service.ts::RevisionModeService.enter
  - schedule-orchestration.service.ts::ScheduleOrchestrationService.result$ → dashboard side-effects
touches:
  - HTTP: PlanningApi (listCycles, compare, clashDiff, listSubmissions, submissionInsights, submissionInsightDetail, pendingSummaries, createCycle, updateStatus, actualize, importBaseline, carryForward, submitPlan, submitAllPending, approveSubmission, approveAllSubmitted, requestRevision), RevisionApi (loadRevision, listTimeline), ApiService (scheduleGroupApi, createTokenSchedule, createPlantSchedule, createAreaSchedule, getBuildingAtPoint), AreaApi (mapFeatureToArea)
  - WebSocket: planning_cycle_updated, planning_actualized, planning_carry_forward, planning_baseline_imported, planning_submission_updated, planning_submissions_bulk_updated, entity_updated, entity_created, entity_deleted
external:
  - PlanningApi
  - RevisionApi
  - ApiService
  - AreaApi
  - WebSocketService
  - DataLoadService
  - EntityService
  - DeliveryService
  - EntitySeverityService
  - SiteContextService
  - MessageService
  - ModalService
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Unified source of truth for all time-based UI state: selected date, shift, scrubber minute, and derived datetime windows for API queries and entity visibility. Drives planning cycle workflows (create, submit, compare, actualize, import baseline, carry forward) and revision mode for historical snapshots.

## Interface
- `services/temporal-context.service.ts::TemporalContextService` — `_viewDateTime`, `_selectedDate`, `_selectedShift`, `_scrubberMinutes`, `_availableShifts`, `_viewState`. Emits `context$`, `requiredFetches$`, `creationContext$`, `effectiveWorkDate$`.
- `services/temporal-context.service.ts::TemporalInputs` — Inputs that drive all temporal computations.
- `services/temporal-context.service.ts::FetchSpec` — Specification for a single data fetch (shiftId + workDate).
- `services/temporal-context.service.ts::CreationContext` — Defaults for creating a new entity at the current time.
- `services/temporal-context.service.ts::TemporalContext` — Complete computed temporal context.
- `services/planning-cycle.service.ts::PlanningCycleService` — Tracks active cycle, compare mode, compare data, submission workflow, and clash diff.
- `services/planning-view-mode.service.ts::PlanningViewModeService` — Derives `PlanningViewMode` (`editing` | `review_submitted` | `comparing`) and read-only gating from `PlanningCycleService.appMode$`.
- `services/revision-mode.service.ts::RevisionModeService` — Historical snapshot mode with LRU cache (max 20). Swaps per-type streams while enabled; live WS events dropped.
- `services/revision-timeline.service.ts::RevisionTimelineService` — Audit-timeline cursor: entries, current index, pinned anchor for compare mode.
- `services/gantt-computation.service.ts::GanttComputationService` — Converts entities into `GanttItem` positioning and `GanttSegment` aggregates.
- `services/gantt-computation.service.ts::GanttContext` — Context (shift, date, minutes) required for Gantt computation.
- `services/schedule-orchestration.service.ts::ScheduleOrchestrationService` — Coordinates schedule creation, reconciliation, group edit/delete, and occurrence updates.
- `services/schedule-orchestration.service.ts::ScheduleOperationResult` — Structured result emitted after schedule operations.
- `services/time-utility.service.ts::TimeUtilityService` — Parsing, formatting, overnight range detection, shift analysis, query range computation.
- `services/timezone.service.ts::TimezoneService` — Site timezone offset and UTC/local conversions.
- `services/sun-times.service.ts::SunTimesService` — Sunrise/sunset calculation from site map coordinates.
- `services/timeline-operations.service.ts::TimelineOperationsService` — Timeline-specific navigation, scrubber, dock, and lane operations.
- `services/time-mode-resolver.ts::TimeModeResolver` — Resolves time mode from entity timestamps and shift schedules; computes datetime ranges.
- `timeline/timeline.component.ts::TimelineComponent` — Main timeline visualization with scrubber, Gantt, shift bands, and keyboard navigation.
- `dashboard/timeline-bar/timeline-bar.component.ts::TimelineBarComponent` — Top-center date/time bar (compact and expanded).
- `dashboard/timeline-dock/timeline-dock.component.ts::TimelineDockComponent` — Resizable dock with weather, Gantt, and clash lanes.
- `dashboard/planning-panel/planning-panel.component.ts::PlanningPanelComponent` — Cycle list, submissions, and coordinator actions.
- `dashboard/planning-panel/planning-panel.store.ts::PlanningPanelStore` — Local signals for cycle/submission view state and side effects.
- `types/planning.types.ts` — `PlanningCycle`, `PlanningCycleStatus`, `AppViewMode`, `CompareLayout`, `ContractorSubmission`, `SubmissionSummary`, `CompareResult`, `ClashDiffResult`, `PendingEntityIdSets`, `BulkSubmitResult`.
- `types/gantt.types.ts` — `GanttItem`, `GanttSegment`, `AggregateSegment`.
- `types/schedule.types.ts` — `ShiftOccurrence`, `OccurrencePayload`, `ScheduleGroupUpdate`, `ScheduleCreateResponse`, `ScheduleReconcileResponse`.

## State
- `services/temporal-context.service.ts::TemporalContextService` — `_viewDateTime`, `_selectedDate`, `_selectedShift`, `_scrubberMinutes`, `_availableShifts`, `_viewState`. Midnight-crossing tracking fields gate auto-date-advance.
- `services/planning-cycle.service.ts::PlanningCycleService` — `_cycles`, `_appMode`, `_compareLayout`, `_planPreviewTarget`, `_compareDataCache`, `_clashDiffCache`, `_userOverrodeMode`.
- `services/revision-mode.service.ts::RevisionModeService` — `_enabled$`, `_snapshot$`, `_compareSnapshots$`, `_cache` (LRU max 20).
- `services/gantt-computation.service.ts::GanttComputationService` — `_cachedGanttItems`, `filteredItemCache`, `fullDayItemsCache`.
- `services/schedule-orchestration.service.ts::ScheduleOrchestrationService` — `pendingScheduleAction`, `pendingScheduleGroupMove`.
- `dashboard/planning-panel/planning-panel.store.ts::PlanningPanelStore` — `cycles`, `submissions`, `submissionRows`, `selectedCycleId`, `pendingSummaryMap`, `actualizeCycleId`, `closeCycleId`, `carryForwardTargetId`, `newCycleAdoptExisting`, plus loading flags.

## Internals
- Temporal derivation pipeline — `services/temporal-context.service.ts::TemporalContextService.computeContext` derives `requiredFetches`, `creationContext`, `effectiveWorkDate`, and shift portion flags from the five input subjects. `computeRequiredFetches` loads the selected shift, the active shift, other overnight shifts (both dates), and any days visible from pan. `setScrubberMinutes` detects midnight crossing on overnight shifts and auto-advances `_selectedDate` only when the shift is unchanged and at least one scrubber change has already happened with this shift.
- Planning cycle workflow — `services/planning-cycle.service.ts::PlanningCycleService` loads cycles per site via `PlanningApi.listCycles`. `activeCycle$` finds the cycle overlapping the selected date using `cycleOverlapsCalendarDate`, which uses lexicographic ISO string comparison and allocates no Date objects. Default `appMode` auto-applies `editing_plan` for `planning` status and `editing_actual` otherwise, unless `_userOverrodeMode` is true. Compare data and clash diff are fetched on demand and cached by cycle id. Submission insights are loaded in one batch; pending summaries are refreshed via `auditTime(300)` on entity streams. WebSocket planning/entity events invalidate caches and trigger refreshes.
- Revision mode snapshot loading — `services/revision-mode.service.ts::RevisionModeService.enter` flips `_enabled$` before the fetch so WS/edit gates engage immediately. Snapshots are cached by `${siteId}|${atTime}` using full ISO precision (max 20 LRU). Per-type streams (`workers$`, `plants$`, `features$`, `areas$`, `deliveries$`) filter by `isEntityActiveAt` against `TemporalContextService.viewDateTime$`. `enterCompare` loads two snapshots and builds a `SplitMapViewModel` via `buildRevisionCompareViewModel`. Single-snapshot and compare modes are mutually exclusive.
- Gantt math — `services/gantt-computation.service.ts::GanttComputationService.computeGanttItems` and `computeGanttItemsForFullDay` convert entities to `GanttItem` positions. Datetime-model entities use `computeGanttBoundsFromDatetime`; legacy entities use shift analysis and portion logic. Memoisation via `filteredItemCache` and `fullDayItemsCache` keyed by signature; datetime-model signatures omit `currentMinutes` so steady scrubber drags are all cache hits. `computeGanttSegments` collects all boundary minutes, sorts them, and counts active items per segment.
- Schedule orchestration — `services/schedule-orchestration.service.ts::ScheduleOrchestrationService` gates grouped edits via `showScheduleScopeIfGrouped` → `handleScheduleActionResult` dispatches to single-entity or group operations. Group delete fetches siblings and records compound undo. Group edit/reconcile/convert applies `ScheduleGroupUpdate` with optimistic patches that are reverted on error. Building checks for group moves/polygons use `buildingCheckWithFallback` and `classifyBuildingCheck`; multi-level buildings prompt via the level-selector modal and complete via `completePendingScheduleGroupMove`. Batch schedule creation (`confirmScheduleCreation`, `createPlantScheduleFromModal`, `createWorkerScheduleFromModal`, `createAreaScheduleFromModal`) resolves `planningCycleId` from `PlanningCycleService.getCycleIdForCreation$`.
- Time utilities — `services/time-utility.service.ts::TimeUtilityService` parses HH:MM and ISO timestamps to site-local minutes via `TimezoneService`. `isOvernightRange`, `isTimeInRange`, `findShiftCoveringTime`, `calculateEffectiveWorkDate`, and `computeShiftQueryRange` handle shift math. `TimezoneService` is the single boundary for UTC↔site-local conversions; `SunTimesService` computes sunrise/sunset from site map latitude and day of year.

## Touches
- HTTP: `PlanningApi` (cycles, compare, clash diff, submissions, insights, pending summaries, create/update/actualize/import/carry-forward/submit/approve/request-revision), `RevisionApi` (load revision, timeline), `ApiService` (schedule group CRUD, batch schedule creation, building-at-point), `AreaApi` (feature-to-area mapping).
- WebSocket: `planning_cycle_updated`, `planning_actualized`, `planning_carry_forward`, `planning_baseline_imported`, `planning_submission_updated`, `planning_submissions_bulk_updated`, `entity_updated`, `entity_created`, `entity_deleted`.

## Gotchas
- `cycleOverlapsCalendarDate` uses lexicographic ISO string comparison → zero Date allocation in the hot path.
- Midnight crossing auto-advance only fires when the shift is unchanged and `_scrubberChangedWithCurrentShift` is true → prevents false positives from programmatic state setup.
- Revision cache key uses full ISO timestamp → truncating to minute would alias distinct audit ticks.
- Gantt memoisation: datetime-model signatures exclude `currentMinutes` → steady scrubber drag is all cache hits; legacy signatures include portion analysis and may recompute.
- `TemporalContextService.context$` includes `_viewState` → panning across days triggers data loads for visible days without changing `selectedDate`.
- `PlanningCycleService.getCycleIdForCreation$` returns `undefined` in `editing_actual` with a draft cycle → forces baseline creation outside the plan scope.
- `RevisionModeService.guardEdit` returns `true` when enabled → all editing entry points must short-circuit; the toast text is centralised so it stays identical everywhere.
- `ScheduleOrchestrationService` applies optimistic updates to loaded siblings before the API call; on error it reverts via `updateLocal` with the pre-call snapshots.
- `TimezoneService.siteTz` is the single source of truth for site timezone → any code calling `getUTCHours` on application data is a bug.
