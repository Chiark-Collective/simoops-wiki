---
service: ui
summary: Selection state, filtering, visibility, centering, hidden entities, and area interaction.
paths:
  - src/app/services/selection.service.ts
  - src/app/services/selection-filter.service.ts
  - src/app/services/filtered-entity-cache.service.ts
  - src/app/services/hover-state.service.ts
  - src/app/services/entity-visibility.service.ts
  - src/app/services/entity-centering.service.ts
  - src/app/services/hidden-entities.service.ts
  - src/app/services/area-feature-interaction.service.ts
  - src/app/services/area-feature-types.ts
  - src/app/services/visibility-settings.service.ts
  - src/app/services/entity-interaction-orchestrator.service.ts
flows: []
touches:
  - localStorage
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Unified selection and visibility subsystem. `SelectionService` manages typed single-entity and `SpatialEntity` multi-selection with tool state. `FilteredEntityCacheService` combines temporal visibility, hidden entities, and plan-state filtering into stable cached arrays. `EntityVisibilityService` produces reactive filtered streams for tokens, plants, and areas. `AreaFeatureInteractionService` coordinates area selection, vertex editing, hole cutting, and layer operations.

## Interface
- `services/selection.service.ts::SelectionService` — Typed single-entity selection (worker, plant, feature, road, poi), spatial multi-selection with add/toggle modes, selection tools (box, lasso), and clear operations.
- `services/selection.service.ts::getSelectionMode` — Maps Shift/Ctrl/Meta modifiers to `add`/`toggle`/`single`.
- `services/selection-filter.service.ts::SelectionFilterService` — Client-side filtering engine supporting type, contractor, planning cycle, and SmartGroup query selection.
- `services/filtered-entity-cache.service.ts::FilteredEntityCacheService` — Three-layer pipeline producing stable visible/hidden/clash entity arrays with plan-state and revision-mode awareness.
- `services/hover-state.service.ts::HoverStateService` — Hover entity and clash popup state.
- `services/entity-visibility.service.ts::EntityVisibilityService` — Reactive streams `visibleTokens$`, `visiblePlants$`, `visibleAreas$`, `activeFeatures$`, and temporal-only clash streams.
- `services/entity-centering.service.ts::EntityCenteringService` — Map camera centering on workers, plants, areas, roads, PoIs, and active features.
- `services/hidden-entities.service.ts::HiddenEntitiesService` — Session-only per-type hidden ID tracking with toggle, show, and show-all operations.
- `services/area-feature-interaction.service.ts::AreaFeatureInteractionService` — Area selection, vertex edit coordination, hole cutting, undo cuts, feature type changes, layer deletion, and building edit routing.
- `services/area-feature-types.ts::ACTIVE_AREA_FEATURE_TYPES` — Canonical set of active area feature types (`exclusion`, `laydown`, `work_area`).
- `services/visibility-settings.service.ts::VisibilitySettingsService` — Opacity, color, and misc display settings with localStorage persistence.
- `services/entity-interaction-orchestrator.service.ts::EntityInteractionOrchestrator` — Routes entity clicks on the map to selection, building/floor coordination, and panel state updates.

## State

### Selection
- `services/selection.service.ts::SelectionService` maintains six `BehaviorSubject` selections: `_selectedToken`, `_selectedPlant`, `_selectedActiveFeature`, `_selectedRoad`, `_selectedPoi`, and `_selection` (primary `SpatialEntity`). `_multiSelection` holds a `Map<string, SpatialEntity>` for add/toggle modes. `_activeTool` drives box/lasso state.
- Typed selection is mutually exclusive: selecting one type → `clearOtherTypes` nulls the other five.
- `selectedEntityType$` is derived manually (not `combineLatest`) to avoid extra emissions.

### Hover
- `services/hover-state.service.ts::HoverStateService` stores `_hoveredEntity` and `_hoveredEntityClashes` as `BehaviorSubject`s.

### Hidden entities
- `services/hidden-entities.service.ts::HiddenEntitiesService` tracks hidden IDs per type in `_hiddenTokens`, `_hiddenPlants`, `_hiddenAreas`, `_hiddenRoads` (`BehaviorSubject<Set<string>>`).
- Hidden entities still participate in clash detection ⟂ they are only removed from rendering.

### Visibility settings
- `services/visibility-settings.service.ts::VisibilitySettingsService` persists `_settings` (`BehaviorSubject<VisibilitySettings>`) to `localStorage` under key `simoops_visibility_settings`. Loaded settings are merged with defaults to handle schema evolution.

### Filtered cache
- `services/filtered-entity-cache.service.ts::FilteredEntityCacheService` stores:
  - Layer 2 (time-filtered): `_visibleTokens`, `_visiblePlants`, `_visibleAreas`
  - Layer 3 (fully filtered): `_cachedVisibleTokens`, `_cachedVisiblePlants`, `_cachedVisibleAreas`, `_cachedVisibleRoads`
  - Hidden mirrors: `_cachedHiddenTokens`, `_cachedHiddenPlants`, `_cachedHiddenFeatures`, `_cachedHiddenRoads`
  - Clash-only (temporal, no hidden): `_clashTokens`, `_clashPlants`, `_clashAreas`
  - Mode state: `_appMode`, `_pendingIds`, `_activeCycleId`, `_revisionEnabled`
- `_cacheUpdateCallbacks` array supports multiple subscribers for change-detection scheduling.

### Visibility reactivity
- `services/entity-visibility.service.ts::EntityVisibilityService` caches `_cachedActiveFeatures` and `_cachedLayerMap` from subscriptions. `sharedContext$` debounces `TemporalContextService.context$` to 16 ms and fans out via `shareReplay` so all visibility streams emit one coordinated frame per tick.

## Internals

### Selection routing
- `services/entity-interaction-orchestrator.service.ts::EntityInteractionOrchestrator.selectActiveFeature` is three-phase: `engageContext` (building-focus, contractual) → `isReselectionInVertexEdit` guard → `applySelection` (panel open, message, vertex-edit auto-start). Contractual effects must live in `engageContext`; anything in `applySelection` is skipped on re-selection during vertex edit.
- `selectTokenFromList` uses `getSelectionMode` from the click event to route through `SelectionService.handleSelection` for multi-select support.

### Filtered cache pipeline
- `FilteredEntityCacheService` subscribes to `EntityVisibilityService` streams, `RoadEditorStateService.roads$`, `HiddenEntitiesService` streams, `PlanningCycleService.appMode$`, `PlanningCycleService.activeCyclePendingIds$`, `PlanningCycleService.activeCycle$`, and `RevisionModeService.enabled$`.
- Plan-state filter `entityInMode` is applied in `updateCache` via `filterByMode`. `STATIC_REFERENCE_FEATURE_TYPES` (`building`, `zone`) short-circuit the filter → they are always visible regardless of plan state.
- In revision mode (`_revisionEnabled === true`), the plan-state filter is bypassed entirely. Applying live cycle + pending IDs to a historical snapshot would incorrectly drop entities.
- Pending entities are re-tagged with `is_pending=true` so the map can animate their opacity.
- Roads have no temporal or plan-state filtering; only hidden-road IDs apply.

### Visibility stream coordination
- `EntityVisibilityService` constructs `sharedContext$` with `debounceTime(16)` and `shareReplay({ bufferSize: 1, refCount: false })`. This replaces six independent debounce timers that previously jittered the map during scrubber drags.
- `visiblePlants$` calls `suppressInactiveCranes` after temporal + contractor filtering.
- `visibleAreas$` restricts to `ACTIVE_AREA_FEATURE_TYPES`; buildings and zones are excluded from the "areas" stream to prevent the map's area tooltip handler from short-circuiting building tooltips.
- `activeFeatures$` merges layer-based geometadata features and site-level areas (`layer_id` is null). Site-level areas wrap `polygon_wgs84` into multi-polygon format and carry `building_feature_id`/`building_level` for floor-focus routing.
- Temporal-only streams (`temporallyVisibleTokens$`, etc.) ignore contractor visibility so hidden contractors still appear in clash detection.

### Selection filtering
- `SelectionFilterService` mirrors `EntityVisibilityService` streams into synchronous fields (`_visibleTokens`, `_visiblePlants`, `_visibleAreas`, `_visiblePois`) via long-lived `takeUntilDestroyed` subscriptions. Roads are setter-fed (`setVisibleRoads`) to avoid a circular DI cycle with `FilteredEntityCacheService`.
- `evaluateQuery` / `matchesQuery` support nested groups with `and`/`or` combinators. `matchesCriteria` has special handling for `entity_type` on areas: positive operators match `area` OR the `feature_type` subtype; negative operators must match both to exclude.

### Area feature interaction
- `AreaFeatureInteractionService` lazily resolves `EntityModalOrchestrator` and `EntityInteractionOrchestrator` via `injector.get` to break circular DI.
- `selectArea` checks `activeFeatures` first; if found, delegates to the orchestrator. Otherwise it creates a fallback `ActiveFeature`, engages building focus, and auto-starts vertex edit when unlocked and editable.
- `onAreaMoved` and `onVertexEditSaved` check `scheduleOrchestration.showScheduleScopeIfGrouped` before mutating geometry; schedule-grouped areas open the scope modal instead of direct update.
- `_polygonsEqual` guards `onVertexEditSaved` so a click-to-deselect that auto-saves vertex edit with no actual change does not pop the schedule-scope modal.
- `pendingCutsForSelectedFeature` is populated by `refreshPendingCutsFor` and consumed by `cutHoleInArea` / `cutHoleInActiveFeature`.

### Centering
- `EntityCenteringService` requires a registered `MapComponent`. `centerOnEntity` delegates coordinate extraction to `EntityOperationsService.centerPoint`.

## Touches

| resource | how | why |
|---|---|---|
| localStorage | read/write JSON under `simoops_visibility_settings` | persist opacity, color, and misc display settings across sessions |

## Gotchas
- Circular DI `FilteredEntityCacheService` ↔ `SelectionFilterService` is broken by feeding roads via `setVisibleRoads` instead of a stream subscription.
- Circular DI `AreaFeatureInteractionService` ↔ `EntityInteractionOrchestrator` / `EntityModalOrchestrator` is broken by lazy `Injector.get` resolution.
- `entityInMode` returns `true` for `building` and `zone` regardless of `plan_state` or `planning_cycle_id`. Adding a new static-reference feature type requires updating `STATIC_REFERENCE_FEATURE_TYPES` in both frontend and backend.
- Revision mode bypasses the plan-state filter. If `RevisionModeService` is enabled and a snapshot is loaded, `_cachedVisible*` arrays contain the snapshot's full set; mixing live plan-state logic with snapshot data causes empty-map regressions.
- `ACTIVE_AREA_FEATURE_TYPES` must be applied by both live (`EntityVisibilityService`) and revision (`RevisionModeService`) area pipelines. Omitting it in either path causes buildings to leak into area arrays and break map click handlers.
- `SelectionFilterService.matchesCriteria` uses `looseEquals` with case-insensitive string comparison and `==` coercion for numbers/booleans. Pattern matching with `matches` operator auto-detects regex vs glob; invalid regex falls back to substring match.
- `selectActiveFeature` re-selection guard skips `applySelection` when the same feature is clicked during vertex edit. Any side effect that must fire on every click (e.g. building focus) must be placed in `engageContext`, not `applySelection`.
- `EntityVisibilityService.sharedContext$` uses `refCount: false` so the shared stream stays hot even when all consumers unsubscribe momentarily. This prevents re-initialization cost but keeps a permanent subscription.
