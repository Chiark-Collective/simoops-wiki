---
service: ui
summary: MapLibre host, event wiring, source management, and subscription orchestration.
paths:
  - src/app/map/README.md
  - src/app/map/map.component.ts
  - src/app/map/map.component.html
  - src/app/map/map-event-wiring.ts
  - src/app/map/map-source-manager.ts
  - src/app/map/map-source-utils.ts
  - src/app/map/map-subscription-orchestrator.ts
  - src/app/map/map-bounds.ts
  - src/app/map/map-building-focus-coordinator.ts
  - src/app/services/area-feature-types.ts
  - src/app/services/entity-visibility.service.ts
flows: []
touches:
  - MapLibre GL
  - DOM
external: []
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose
Hosts the MapLibre GL map, wires pointer/keyboard interactions, manages GeoJSON sources, and coordinates reactive subscriptions for the SimOops dashboard map. Source updates migrate through `RecreatableMapSource` to work around Zone.js/MapLibre empty-source bugs. Building focus and indoor visibility are delegated to `MapBuildingFocusCoordinator` and `BuildingVisibilityPolicy`.

## Interface
- `map/map.component.ts::MapComponent` — `@Component` selector `app-map`; initialises map, orchestrates helpers, exposes `@Output() mapReady`.
- `map/map-event-wiring.ts::MapEventWiring` — Binds all MapLibre event listeners via the `MapEventWiringHost` interface.
- `map/map-source-manager.ts::MapSourceManager` — Per-domain GeoJSON source updates. Delegates to `RecreatableMapSource` for sources that need recreation on empty→populated transitions.
- `map/map-source-utils.ts::RecreatableMapSource` — Typed wrapper around a GeoJSON source that recreates source+layers on the first empty→populated transition, then replays logged `setFilter`/`setFeatureState`/`setLayoutProperty`/`setPaintProperty` calls. Caps replay log at 10,000 entries with 5,000 warning threshold.
- `map/map-subscription-orchestrator.ts::MapSubscriptionOrchestrator` — Centralises RxJS subscriptions for selection, display config, entity data, label styles, creation mode, vertex ops, presence viewports, alerts, and contractor logo sync.
- `map/map-bounds.ts::computeOverrideEntityBounds` — Pure helper building `LngLatBounds` from override collections.
- `map/map-bounds.ts::computeOverrideEntityCacheKey` — Stable cache key for the auto-fit retry loop.
- `map/map-building-focus-coordinator.ts::MapBuildingFocusCoordinator` — Owns selected building, focused floor, and hovered building state; drives map paint updates and synchronous repaints. Delegates floor visibility decisions to `computeFloorDisplayDecision`.
- `map/map-building-focus-coordinator.ts::BuildingFocusHost` — Interface supplying map, features, visibility settings, repaint hooks, and `revisionModeActive` flag.
- `map/map-building-focus-coordinator.ts::isFeatureFloorHidden` — Pure function checking whether a feature is hidden by floor-based opacity.
- `services/map-interaction.service.ts::MapInteractionService` — `@Injectable` event bus.
- `services/map-event-dispatch.service.ts::MapEventDispatchService` — `@Injectable` dispatcher routing interaction events to services.
- `services/area-feature-types.ts::ACTIVE_AREA_FEATURE_TYPES` — Canonical set of work-assignment feature types (`exclusion`, `laydown`, `work_area`) shared by live and revision streams.
- `services/entity-visibility.service.ts::EntityVisibilityService` — Reactive entity visibility filtering. Imports `ACTIVE_AREA_FEATURE_TYPES` from the canonical location; `visibleAreas$` filters to these types so buildings and zones do not leak into area-list streams.

## State
### MapComponent
- `map?: MlMap` — live instance.
- `zoom`, `currentMetresPerPixel`, `scaleLabel`, `scaleBarWidthPx`, `scaleBarLeftPanelOpen` — template-bound scale bar.
- `rasterMinZoom`, `rasterMaxZoom` — tile source bounds.
- `mapInitializing` — guard against concurrent `initMap`.
- `resizeObserver` — container resize watcher.
- `lastAppliedAutoFitEntitiesKey`, `autoFitRetryTimeout` — auto-fit dedup / retry.
- `hoverTooltipHtml` — fixed-position tooltip HTML.
- `editingFeatureId` — feature hidden during vertex edit.
- `previousSelectedAreaIds` — prior selection set for `setFeatureState` diffing.
- `selectedTokenId` — local token selection mirror.
- `_entitySeverityCache` — clash severity map, invalidated on `clashes` change.
- `savedLayerVisibility`, `savedSharedLayerFilters` — stashed state during badge-hover highlight.
- `dirtyFlags` — RAF-scheduled update batch.

### MapEventWiring
- `prevAreaClickPos`, `lastAreaClickPos`, `prevAreaClickPoint`, `lastAreaClickPoint` — pixel-distance state for double-click vs rapid vertex placement.

### MapSourceManager
- `map: MlMap | undefined` — set once via `setMap`.
- `sources: Map<string, RecreatableMapSource>` — lazily populated per source ID, cleared on map change.

### MapSubscriptionOrchestrator
- `subs` — teardown bag.
- `cacheTeardown` — filtered entity cache callback.
- `prevMultiSelectedIds` — diff optimisation for area-only multi-selection changes.

## Internals
### MapLibre initialisation
`map/map.component.ts::ngAfterViewInit` → `initMap`. If `hasMapSource()` is true, constructs `maplibregl.Map` inside `ngZone.runOutsideAngular` to avoid per-frame change detection. Style contains a raster source (COG tilejson or XYZ) and a background layer. Navigation controls added. On `map.on('load')`, `addSourcesAndLayers` registers MVT / GeoJSON sources, patterns, icons, and ordered layers. Controllers instantiated. `mapReady` emitted.
- `map/map-source-utils.ts::mapEventSignal<T>()` — Bridges MapLibre events into Angular signals, solving outside-zone `markForCheck` timing issues.

### Event wiring lifecycle
`map/map-event-wiring.ts::bindAll` called once inside the load handler (gated by `!passiveMirrorMode`). Registers click, mousedown, mouseup, mousemove, dblclick, and contextmenu handlers on specific layers. Hit detection uses `queryRenderedFeatures` with explicit layer lists. Right-click drag distance >5px suppresses context menu and triggers rotation. Area double-click finish checks pixel distance ≤5px to avoid mistaking rapid vertex placement for an intentional double-click.

### Source update batching
`map/map.component.ts::ngOnChanges` sets flags on a `MapDirtyFlags` object instead of calling expensive updates directly. `scheduleMapUpdate` delegates to `MapDirtyFlagScheduler`, which flushes via a single `requestAnimationFrame`. Each flag maps to one `updateXxx` method, coalescing simultaneous input changes.

### Subscription orchestration
`map/map.component.ts::buildSubscriptionOrchestrator` constructs `MapSubscriptionOrchestrator` with a `MapSubscriptionHost` (the component) and `MapSubscriptionServices` (injected services). `start()` in `ngAfterViewInit` wires selection, display config, and entity data. After map load, `startLabelStyles`, `startCreationMode`, `startVertexOps`, `startPresenceViewports`, and `startAlerts` wire map-bound subs. Each sub mutates dirty flags or invokes host callbacks. `destroy()` unsubscribes all.

### Auto-fit retry loop
`map/map.component.ts::applyAutoFitToOverrideEntities` calls `map/map-bounds.ts::computeOverrideEntityBounds` to build `LngLatBounds` from override inputs. A cache key from `computeOverrideEntityCacheKey` skips redundant fits. Single-point bounds → `easeTo` zoom 17; multi-point → `fitBounds` maxZoom 18. A 200ms timeout and `map.once('idle')` force re-fit to catch late geometry loads.

### RecreatableMapSource abstraction
`map/map-source-utils.ts::RecreatableMapSource` wraps a GeoJSON source and its dependent layers. On the first empty→populated transition it removes and re-adds the source (working around the Zone.js/MapLibre symbol-layer bug), then replays a logged queue of layout and paint changes so dynamic filters and sizing expressions survive recreation. `MapSourceManager` caches one instance per source ID via `getSource(sourceId, layerIds)`.
- Replay log capped at 10,000 entries; warns at 5,000 to catch pathological hot loops
- Tracks `setFilter`, `setFeatureState`, `setLayoutProperty`, `setPaintProperty` calls and replays after recreation
- `mapEventSignal<T>()` bridges MapLibre events into Angular signals with automatic cleanup via `DestroyRef`

### Building focus coordination
`MapBuildingFocusCoordinator` subscribes to `BuildingFocusService.hoveredBuilding$` and fans out to dirty flags + change detection. `setFocus` triggers `updateBuildingHighlight`, `updateRasterDimming`, and synchronous repaints of beacons, geometadata, and badges. Floor visibility decisions are delegated to `computeFloorDisplayDecision` from `utils/building-visibility-policy.ts`, which receives `revisionModeActive` from the host. When revision mode is active and no floor focus exists, indoor entities surface at full opacity regardless of `indoorMode`; an active floor focus still dims off-floor entities.

### Area feature type filtering
`services/area-feature-types.ts::ACTIVE_AREA_FEATURE_TYPES` is the canonical set of work-assignment types (`exclusion`, `laydown`, `work_area`). `EntityVisibilityService.visibleAreas$` and `RevisionModeService.areas$` both filter to this set, preventing buildings and zones from leaking into the visible-areas stream that drives map hover/click handlers and the Active Areas panel.

## Touches
| resource | how | why |
| MapLibre GL | `maplibregl.Map`, sources, layers, controls, popups, event system | renders map and handles interactions |
| DOM | canvas container, `ResizeObserver`, drag-and-drop file events, cursor styles | hosts canvas, adapts layout, enables floor-plan drop |

## Gotchas
- `ngZone.runOutsideAngular` during MapLibre construction is required; without it Zone.js CD runs at 60fps and mobile stutters.
- `passiveMirrorMode === true` ⟂ event wiring, drag controllers, touch adapter, ephemeral throttler, viewport broadcast, and shift+wheel intercept.
- Zone.js / MapLibre bug: symbol layers on GeoJSON sources that start empty fail after `setData`. `RecreatableMapSource` removes and re-adds the source on the first empty→populated transition and replays logged layout/paint changes. Affected sources include delivery pins, inactive cranes, building badges, geometadata.
- Source recreation resets dynamic filters and layout properties; `RecreatableMapSource` replays the change log so callers do not need to re-apply visibility and selection state manually.
- `highlightLayerType` uses `setLayoutProperty('visibility')` instead of opacity dimming because the pending-pulse RAF loop overwrites paint expressions.
- Building badges are prerendered canvas images keyed by entity count + area count to avoid per-frame text rendering.
- `applyAutoFitToOverrideEntities` key is derived from entity IDs; geometry mutations without ID changes do not re-trigger auto-fit.
- `mapInitializing === true` ⟂ `mapReady` emission.
- `BuildingFocusHost.revisionModeActive` replaces the earlier `bypassFloorDimming` flag. Floor focus dimming now applies in every mode; revision mode indoor visibility is handled by `BuildingVisibilityPolicy`.
- Buildings and zones are excluded from `ACTIVE_AREA_FEATURE_TYPES`. Letting them through causes `map-event-wiring.ts` tooltip handlers to mistake building polygons for areas, swallowing building-hover/click events.

(End of file - total 138 lines)
