---
service: ui
summary: MapLibre host, event wiring, source management, and subscription orchestration.
paths:
  - src/app/map/README.md
  - src/app/map/map.component.ts
  - src/app/map/map.component.html
  - src/app/map/map-event-wiring.ts
  - src/app/map/map-source-manager.ts
  - src/app/map/map-subscription-orchestrator.ts
  - src/app/map/map-bounds.ts
flows: []
touches:
  - MapLibre GL
  - DOM
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Hosts the MapLibre GL map, wires pointer/keyboard interactions, manages GeoJSON sources, and coordinates reactive subscriptions for the SimOops dashboard map.

## Interface
- `map/map.component.ts::MapComponent` — `@Component` selector `app-map`; initialises map, orchestrates helpers, exposes `@Output() mapReady`.
- `map/map-event-wiring.ts::MapEventWiring` — Binds all MapLibre event listeners via the `MapEventWiringHost` interface.
- `map/map-source-manager.ts::MapSourceManager` — Per-domain GeoJSON source updates.
- `map/map-subscription-orchestrator.ts::MapSubscriptionOrchestrator` — Centralises RxJS subscriptions for selection, display config, entity data, label styles, creation mode, vertex ops, presence viewports, and alerts.
- `map/map-bounds.ts::computeOverrideEntityBounds` — Pure helper building `LngLatBounds` from override collections.
- `map/map-bounds.ts::computeOverrideEntityCacheKey` — Stable cache key for the auto-fit retry loop.
- `services/map-interaction.service.ts::MapInteractionService` — `@Injectable` event bus.
- `services/map-event-dispatch.service.ts::MapEventDispatchService` — `@Injectable` dispatcher routing interaction events to services.

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

### MapSubscriptionOrchestrator
- `subs` — teardown bag.
- `cacheTeardown` — filtered entity cache callback.
- `prevMultiSelectedIds` — diff optimisation for area-only multi-selection changes.

## Internals
### MapLibre initialisation
`map/map.component.ts::ngAfterViewInit` → `initMap`. If `hasMapSource()` is true, constructs `maplibregl.Map` inside `ngZone.runOutsideAngular` to avoid per-frame change detection. Style contains a raster source (COG tilejson or XYZ) and a background layer. Navigation controls added. On `map.on('load')`, `addSourcesAndLayers` registers MVT / GeoJSON sources, patterns, icons, and ordered layers. Controllers instantiated. `mapReady` emitted.

### Event wiring lifecycle
`map/map-event-wiring.ts::bindAll` called once inside the load handler (gated by `!passiveMirrorMode`). Registers click, mousedown, mouseup, mousemove, dblclick, and contextmenu handlers on specific layers. Hit detection uses `queryRenderedFeatures` with explicit layer lists. Right-click drag distance >5px suppresses context menu and triggers rotation. Area double-click finish checks pixel distance ≤5px to avoid mistaking rapid vertex placement for an intentional double-click.

### Source update batching
`map/map.component.ts::ngOnChanges` sets flags on a `MapDirtyFlags` object instead of calling expensive updates directly. `scheduleMapUpdate` delegates to `MapDirtyFlagScheduler`, which flushes via a single `requestAnimationFrame`. Each flag maps to one `updateXxx` method, coalescing simultaneous input changes.

### Subscription orchestration
`map/map.component.ts::buildSubscriptionOrchestrator` constructs `MapSubscriptionOrchestrator` with a `MapSubscriptionHost` (the component) and `MapSubscriptionServices` (injected services). `start()` in `ngAfterViewInit` wires selection, display config, and entity data. After map load, `startLabelStyles`, `startCreationMode`, `startVertexOps`, `startPresenceViewports`, and `startAlerts` wire map-bound subs. Each sub mutates dirty flags or invokes host callbacks. `destroy()` unsubscribes all.

### Auto-fit retry loop
`map/map.component.ts::applyAutoFitToOverrideEntities` calls `map/map-bounds.ts::computeOverrideEntityBounds` to build `LngLatBounds` from override inputs. A cache key from `computeOverrideEntityCacheKey` skips redundant fits. Single-point bounds → `easeTo` zoom 17; multi-point → `fitBounds` maxZoom 18. A 200ms timeout and `map.once('idle')` force re-fit to catch late geometry loads.

## Touches
| resource | how | why |
| MapLibre GL | `maplibregl.Map`, sources, layers, controls, popups, event system | renders map and handles interactions |
| DOM | canvas container, `ResizeObserver`, drag-and-drop file events, cursor styles | hosts canvas, adapts layout, enables floor-plan drop |

## Gotchas
- `ngZone.runOutsideAngular` during MapLibre construction is required; without it Zone.js CD runs at 60fps and mobile stutters.
- `passiveMirrorMode === true` ⟂ event wiring, drag controllers, touch adapter, ephemeral throttler, viewport broadcast, and shift+wheel intercept.
- Zone.js / MapLibre bug: symbol layers on GeoJSON sources that start empty fail after `setData`. `updateGeoJsonSourceWithRecreate` removes and re-adds the source on the first empty→populated transition. Affected sources: delivery pins, inactive cranes, building badges, geometadata.
- Source recreation resets dynamic filters and layout properties; callers must re-apply visibility and selection state afterwards.
- `highlightLayerType` uses `setLayoutProperty('visibility')` instead of opacity dimming because the pending-pulse RAF loop overwrites paint expressions.
- Building badges are prerendered canvas images keyed by entity count + area count to avoid per-frame text rendering.
- `applyAutoFitToOverrideEntities` key is derived from entity IDs; geometry mutations without ID changes do not re-trigger auto-fit.
- `mapInitializing === true` ⟂ `mapReady` emission.
