---
trigger: { channel: ui, ref: "revision mode entry" }
services: [ui, backend]
contracts: [ui-backend/http-contract]
external: []
---

## Trigger
User clicks a revision button or timeline entry, or `RevisionTimelineService` steps to a new index.

## Steps
1. Entry: a dashboard component invokes `services/revision-timeline.service.ts::RevisionTimelineService.load(siteId, since, until)` or `services/revision-mode.service.ts::RevisionModeService.enter(siteId, atTime)` directly.
2. `RevisionTimelineService.load` fetches the audit timeline via `services/revision.api.ts::RevisionApi.listTimeline`, populates `_entries$`, sets `_currentIndex$` to 0, and emits `_loadRequest$`.
3. `RevisionTimelineService` constructor debounces `_loadRequest$` with `debounceTime(STEP_DEBOUNCE_MS)` and switches to `_loadForCurrentState`; `switchMap` cancels in-flight fetches.
4. `_loadForCurrentState` decides single vs compare: if `_pinnedIndex$` is set and differs from `_currentIndex$`, it calls `RevisionModeService.enterCompare(siteId, entries[left].timestamp, entries[right].timestamp)` with normalised order; otherwise `RevisionModeService.enter(siteId, entries[idx].timestamp)`.
5. `RevisionModeService.enter` calls `viewMode.enterRevision(atTime)` synchronously and clears `_compareSnapshots$` — single-snapshot and compare modes are mutually exclusive.
6. `RevisionModeService.enter` builds a cache key via `services/revision-mode.service.ts::cacheKey` (`${siteId}|${atTime}` with full ISO precision). On cache hit the snapshot is re-inserted and emitted via `_snapshot$`. On miss, `_loading$` becomes `true` and `RevisionApi.loadRevision(siteId, atTime)` is invoked.
7. `RevisionApi.loadRevision` fans out parallel HTTP GETs to backend per-type `/at-time` endpoints (`/workers/at-time`, `/plant/at-time`, `/geometadata/features/at-time`, `/deliveries/at-time`, `/pois/at-time`, `/text-labels/at-time`, `/clashes/at-time`, `/floor-plans/at-time`) plus `/sites/{siteId}/snapshot-revision`. Any child error cancels the entire `forkJoin`.
8. Backend returns historical entity state; `RevisionApi.loadRevision` assembles a `RevisionSnapshot`.
9. `RevisionModeService.enter` stores the snapshot in the LRU `_cache` via `_rememberInCache` (max `CACHE_MAX` = 20, evicting oldest), pushes it into `_snapshot$`, and sets `_loading$` to `false`.
10. With `viewMode.shouldDropLiveEvents$` true, live WebSocket events are dropped: `EntityService.wsBatchUpdateTokens`, `wsBatchUpdatePlants`, and `DataLoadService.forceRefreshEntities` short-circuit while `viewMode.shouldDropLiveEvents` is true.
11. `services/filtered-entity-cache.service.ts::FilteredEntityCacheService` detects read-only mode via `viewMode.shouldBypassPlanFilter$` and swaps from live `EntityVisibilityService` streams to `RevisionModeService` streams (`workers$`, `plants$`, `areas$`) only after `snapshot$` emits non-null.
12. `FilteredEntityCacheService.updateCache` bypasses the plan-state filter (`entityInMode`) when `viewMode.shouldBypassPlanFilter$` is true, because the snapshot already represents the historical truth and live cycle/pending filters would alias distinct states.
13. Per-type revision streams (`workers$`, `plants$`, `features$`, `areas$`, `deliveries$`) combine `_snapshot$` with `services/temporal-context.service.ts::TemporalContextService.viewDateTime$` and filter by `utils/temporal-computation.ts::isEntityActiveAt` using the scrubber view datetime, keeping edit-history time orthogonal to rendered shift/day.
14. `RevisionModeService.features$` deduplicates by `feature.id` (last-write-wins) to guard against overlapping backend `FeatureVersion` rows; `areas$` restricts to `ACTIVE_AREA_FEATURE_TYPES` and maps via `services/area.api.ts::AreaApi.mapFeatureToArea`.
15. `RevisionModeService.plants$` applies `utils/plant-synthesis.ts::suppressInactiveCranes` so overlapping active and synthetic crane rows render a single symbol.
16. `RevisionTimelineService.stepNext`, `stepPrev`, and `jumpTo` update `_currentIndex$` synchronously and emit `_loadRequest$`; the debounced pipeline absorbs rapid input and reloads at the final index.
17. `RevisionTimelineService.pin` sets `_pinnedIndex$`; subsequent loads trigger `RevisionModeService.enterCompare`, which calls `viewMode.enterRevision(atLeft)`, clears `_snapshot$`, loads both snapshots in parallel (cached or via `RevisionApi.loadRevision`), pushes the pair into `_compareSnapshots$`, and sets `_loading$` to `false`.
18. `RevisionModeService.compareViewModel$` combines `_compareSnapshots$` with `TemporalContextService.viewDateTime$` and calls `utils/revision-compare.util.ts::buildRevisionCompareViewModel`, producing a `SplitMapViewModel` with per-side entities filtered by scrubber time and empty diff halos.
19. `map/map-split-compare.component.ts::MapSplitCompareComponent` receives the view model (via `viewModelOverride` or parent binding to `compareViewModel$`) and renders two clipped `<app-map>` instances fed by override inputs (`tokensOverride`, `plantsOverride`, `areasOverride`, `deliveriesOverride`, `geometadataFeaturesOverride`).
20. `services/clash-state.service.ts::ClashStateService.setClashes` silently returns while `viewMode.shouldDropLiveEvents$` is true; the constructor also subscribes to `revisionMode.clashes$` when enabled and pushes them into `_clashes`.
21. `ViewModeService.guardEdit` returns `true` in any read-only mode, causing editing entry points to short-circuit after surfacing a mode-aware info toast via `MessageService`. `RevisionModeService.guardEdit` is deprecated and delegates to the same helper.
22. Exit: `RevisionModeService.exit()` calls `viewMode.exitRevision()`, sets `_snapshot$` and `_compareSnapshots$` to null, and `_loading$` to false. `FilteredEntityCacheService` reverts to live streams; the caller follows with `services/data-load.service.ts::DataLoadService.forceRefreshEntities()` to re-hydrate live state and resume WebSocket processing.

## Side effects
- HTTP GET to backend per-type `/at-time` endpoints (up to 9 parallel calls per snapshot).
- `viewMode.shouldDropLiveEvents$` → `true` gates WS delta application across the app.
- `_snapshot$` / `_compareSnapshots$` emission causes `FilteredEntityCacheService` to rebuild visible/hidden caches and notify subscribers via `_cacheUpdateCallbacks`.
- `TemporalContextService.viewDateTime$` emission causes per-type revision streams to re-filter, producing new arrays for template binding.
- `ViewModeService.guardEdit` emits a mode-aware toast via `MessageService` and blocks the editing operation.
- `MapSplitCompareComponent` writes `simoops_split_width` to `localStorage` on divider drag.

## Failure modes
- Any child of `RevisionApi.loadRevision` fails → `forkJoin` errors, snapshot never loads, `_loading$` stays `true` until next attempt; no partial map is rendered.
- `RevisionTimelineService` rapid stepping → `switchMap` cancels in-flight fetches; only the latest index resolves.
- Cache key truncated to minute precision → distinct audit ticks alias to the same cached snapshot, causing stale data. Full ISO precision is required.
- Mixing live plan-state filter with snapshot data → empty map. `FilteredEntityCacheService` bypasses the filter in revision mode to prevent this.
- Live WS event slips through while `viewMode.shouldDropLiveEvents$` is true → snapshot state could be clobbered by live data. Consumers must check `viewMode.shouldDropLiveEvents` before applying deltas.
- `MapSplitCompareComponent` child map destroyed before `ngOnDestroy` runs → `removeDiffHaloLayer` swallows the MapLibre throw so Angular view-swap does not hang.
