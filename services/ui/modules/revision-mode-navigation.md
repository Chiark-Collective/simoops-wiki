---
service: ui
summary: Historical revision snapshots, compare mode, and timeline-driven navigation.
paths:
  - services/revision-mode.service.ts
  - services/view-mode.service.ts
flows:
  - flows/revision-mode-navigation.md
touches: []
external: []
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose
Owns the historical revision snapshot data and per-type filtered streams. The mode flag lives on `ViewModeService` after G11 Phase 3; this service manages snapshots, caching, and compare-mode state.

## Interface
- `services/revision-mode.service.ts::RevisionModeService` — Loads and caches historical snapshots.
- `services/revision-mode.service.ts::RevisionModeService.enter` — Loads snapshot at `atTime`, calls `viewMode.enterRevision`, clears compare state.
- `services/revision-mode.service.ts::RevisionModeService.exit` — Clears snapshot/compare state, calls `viewMode.exitRevision`.
- `services/revision-mode.service.ts::RevisionModeService.enterCompare` — Loads two snapshots, calls `viewMode.enterRevision`, pushes pair into `_compareSnapshots$`.
- `services/revision-mode.service.ts::RevisionModeService.enabled$` — Derived from `viewMode.state$` (true when `kind === 'revision'`).
- `services/revision-mode.service.ts::RevisionModeService.snapshot$` / `loading$` / `summary$`
- `services/revision-mode.service.ts::RevisionModeService.compareSnapshots$` / `compareViewModel$` — Split-map data model.
- Per-type streams: `workers$`, `plants$`, `features$`, `areas$`, `deliveries$`, `pois$`, `textLabels$`, `clashes$`, `floorPlans$`.
- `services/revision-mode.service.ts::RevisionModeService.guardEdit` — `@deprecated`; delegates to `ViewModeService.guardEdit`.
- `components/revision-picker-modal.component.ts::RevisionPickerModalComponent` — 3-tab modal: "View at moment" (single), "Compare two times" (compare), "Rewind through revisions" (rewind). Prefills from audit-row context when opened via rewind icon.
- `components/entity-history-timeline.component.ts::EntityHistoryTimelineComponent` — Chronological audit-entry timeline with revert button, "View on map" button, rewind button, hover preview, compact mode, and diff table for updated entries.

## State
- `services/revision-mode.service.ts::RevisionModeService._snapshot$` — `BehaviorSubject<RevisionSnapshot | null>`.
- `services/revision-mode.service.ts::RevisionModeService._compareSnapshots$` — `BehaviorSubject<{left, right} | null>`; mutually exclusive with single snapshot.
- `services/revision-mode.service.ts::RevisionModeService._loading$` — `BehaviorSubject<boolean>`.
- `services/revision-mode.service.ts::RevisionModeService._cache` — LRU `Map<string, RevisionSnapshot>` sized to 20 entries, keyed by ``${siteId}|${atTime}`` with full ISO precision.
- Invariant: single-snapshot and compare modes are mutually exclusive.

## Internals
- `_enabled$` removed in Phase 3. `enabled$` derives from `viewMode.state$`.
- `enter()` / `exit()` / `enterCompare()` route mode transitions through `ViewModeService`.
- `guardEdit` is a thin deprecated façade; new callers should use `ViewModeService.guardEdit` directly.
- Per-type streams combine `_snapshot$` with `TemporalContextService.viewDateTime$` and filter by `isEntityActiveAt` to keep edit-history time orthogonal to rendered shift/day.
- `features$` deduplicates by `feature.id` (last-write-wins) to guard against overlapping `FeatureVersion` rows.
- `areas$` filters to `ACTIVE_AREA_FEATURE_TYPES` and maps via `AreaApi.mapFeatureToArea`.
- `plants$` applies `suppressInactiveCranes` so overlapping active and synthetic crane rows render one symbol.

## Gotchas
- Any child failure in `RevisionApi.loadRevision` cancels the entire `forkJoin`; no partial snapshot is rendered.
- Cache key uses full ISO precision. Truncating to minute aliases distinct audit ticks.
- `guardEdit` is deprecated. Direct use of `ViewModeService.guardEdit` covers all read-only modes with mode-aware toasts.
- `FilteredEntityCacheService` bypasses the live plan-state filter when `viewMode.shouldBypassPlanFilter$` is true, because snapshot data is already historical truth.
- Revision picker prefill: single = view AT timestamp; compare = anchor left on timestamp, right on now; rewind = 24h window centred on timestamp
- Entity history timeline `showHoverPreview` emits `previewHoverStart`/`previewHoverEnd` so parent can flash map to revision; disabled by default in properties panel to keep timeline passive
