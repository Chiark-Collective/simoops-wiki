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
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Unified source of truth for all time-based UI state: selected date, shift, scrubber minute, and derived datetime windows for API queries and entity visibility. Drives planning cycle workflows (submit, compare, import baseline) and revision mode for historical snapshots.

## Interface
- `services/temporal-context.service.ts::TemporalContextService` — `BehaviorSubject`-driven source of truth for `selectedDate`, `selectedShift`, `scrubberMinutes`. Emits `FetchSpec`, `CreationContext`, `ViewWindowState`, and entity visibility predicates.
- `services/temporal-context.service.ts::TemporalInputs` — Inputs that drive all temporal computations.
- `services/temporal-context.service.ts::FetchSpec` — Specification for a single data fetch (shiftId + workDate).
- `services/temporal-context.service.ts::CreationContext` — Defaults for creating a new entity at the current time.
- `services/planning-cycle.service.ts::PlanningCycleService` — Tracks active planning cycle, compare mode, compare data, and submission workflow.
- `services/planning-view-mode.service.ts::PlanningViewModeService` — Manages `AppViewMode` (`live` | `plan` | `compare`) and derived UI flags.
- `services/revision-mode.service.ts::RevisionModeService` — Historical snapshot mode with LRU cache (max 20). Swaps `FilteredEntityCacheService` to revision streams; live WS events dropped while enabled.
- `services/revision-timeline.service.ts::RevisionTimelineService` — Timeline scrubber for stepping through revision history.
- `services/gantt-computation.service.ts::GanttComputationService` — Converts entities into `GanttItem` positioning and `GanttSegment` aggregates for timeline bars.
- `services/gantt-computation.service.ts::GanttContext` — Context (shift, date, minutes) required for Gantt computation.
- `services/schedule-orchestration.service.ts::ScheduleOrchestrationService` — Coordinates schedule creation, reconciliation, and occurrence updates across entities.
- `services/time-utility.service.ts::TimeUtilityService` — Parsing, formatting, overnight range detection, shift analysis.
- `services/timezone.service.ts::TimezoneService` — Site timezone offset and UTC/local conversions.
- `services/sun-times.service.ts::SunTimesService` — Sunrise/sunset calculation from coordinates.
- `services/timeline-operations.service.ts::TimelineOperationsService` — Timeline-specific entity operations (schedule editing, drag-drop).
- `services/time-mode-resolver.ts::TimeModeResolver` — Resolves time mode from route or context.
- `timeline/timeline.component.ts::TimelineComponent` — Main timeline visualization component.
- `types/planning.types.ts` — `PlanningCycle`, `PlanningCycleStatus`, `SubmissionSummary`, `CompareResult`, `BulkSubmitResult`, etc.
- `types/gantt.types.ts` — `GanttItem`, `GanttSegment`, `AggregateSegment`.
- `types/schedule.types.ts` — `ShiftSchedule`, `ScheduleGroupUpdate`, `OccurrencePayload`.
