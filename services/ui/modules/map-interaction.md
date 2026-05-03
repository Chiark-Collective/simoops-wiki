---
service: ui
summary: Drag handlers, vertex editing, context menus, selection tools, touch adapter, pan controls, and interaction services.
paths:
  - src/app/map/map-drag.ts
  - src/app/map/map-drag-worker.ts
  - src/app/map/map-drag-plant.ts
  - src/app/map/map-drag-area.ts
  - src/app/map/map-drag-road.ts
  - src/app/map/map-drag-types.ts
  - src/app/map/map-vertex-edit.ts
  - src/app/map/map-context-menu.ts
  - src/app/map/map-context-menu.component.ts
  - src/app/map/map-selection-tools.ts
  - src/app/map/map-touch-adapter.ts
  - src/app/map/map-pan.ts
  - src/app/services/map-event-dispatch.service.ts
  - src/app/services/map-interaction.service.ts
  - src/app/services/map-interaction.types.ts
  - src/app/utils/intersection.ts
flows: []
touches: []
external:
  - maplibre-gl
  - turf-js
last_verified_commit: f9606469ce367229c5c91e03c3ba917779015030
---

## Purpose
Coordinates all user interactions on the map: entity dragging, polygon vertex editing, context menus, multi-selection, touch gestures, middle-mouse panning, and the typed event bus that feeds the dashboard.

## Interface

### Drag system
- `app/map/map-drag.ts::MapDragController` — Coordinates drag state across entity types; exposes `startTokenDrag`, `startPlantDrag`, `startAreaDrag`, `startRoadDrag`, and touch-drag forwarding.
- `app/map/map-drag-worker.ts::WorkerDragHandler` — Token move and radius-resize drag with live clash preview.
- `app/map/map-drag-plant.ts::PlantDragHandler` — Plant move, arc-handle rotation, and radius-handle resize.
- `app/map/map-drag-area.ts::AreaDragHandler` — Area polygon translation and temp-vertex drag during creation.
- `app/map/map-drag-road.ts::RoadDragHandler` — Whole-road translation.
- `app/map/map-drag-types.ts::DragContext` — Shared map/callback/time context and visual helpers for all drag sub-handlers.
- `app/map/map-drag-types.ts::DragCallbacks` — Host interface consumed by drag handlers.

### Vertex editing
- `app/map/map-vertex-edit.ts::MapVertexEditController` — Polygon vertex editing: click selection, box/lasso multi-select, edge insertion, and OT op broadcast.
- `app/map/map-vertex-edit.ts::VertexEditCallbacks` — Host callbacks for save, cancel, message, and vertex op broadcast.

### Context menus
- `app/map/map-context-menu.ts::MapContextMenuController` — Hit detection, disambiguation routing, right-click drag FSM, and menu event emission.
- `app/map/map-context-menu.component.ts::MapContextMenuComponent` — Standalone `@Component` (signals-based) that renders the context-menu UI. All editing entry points (create, edit, delete, change type, edit shape, delete feature) call `viewMode.guardEdit` before proceeding.

### Selection tools
- `app/map/map-selection-tools.ts::MapSelectionToolsController` — Box and lasso selection with Turf.js polygon intersection; emits selected entities via `SelectionService`.
- `app/map/map-selection-tools.ts::SelectionToolCallbacks` — Host callbacks for entity lists and selection completion.

### Touch & pan
- `app/map/map-touch-adapter.ts::MapTouchAdapter` — Canvas-level touch handlers for long-press context menu and entity drag on mobile.
- `app/map/map-pan.ts::MapMiddlePanController` — Middle-mouse panning (frees left-click for selection).

### Services
- `app/services/map-interaction.service.ts::MapInteractionService` — `@Injectable` central event bus using a typed `Subject<MapInteractionEvent>`.
- `app/services/map-interaction.types.ts::MapInteractionEvent` — Discriminated union covering all 59+ event types.
- `app/services/map-event-dispatch.service.ts::MapEventDispatchService` — `@Injectable` subscriber that dispatches `MapInteractionEvent`s to injected orchestrator services and component callbacks.
- `app/services/map-event-dispatch.service.ts::MapEventCallbacks` — Thin callback interface for events requiring component-local state or ViewChild access.

### Containment utilities
- `app/utils/intersection.ts::computeTokenFeatureIntersections` — Token footprint against place-like features with building/floor gating.
- `app/utils/intersection.ts::computeFeatureContainment` — Enumerates tokens/plants/areas inside a selected feature for the "Contains" panel. Skips `INFRASTRUCTURE_AREA_FEATURE_TYPES` (`building`, `zone`) so only user-drawn activity polygons are listed.
- `app/utils/intersection.ts::aggregateIntersections` / `aggregateFeatureContainment` — Multi-selection roll-ups.

## State

### Drag system
`MapDragController` stores `readOnly` (blocks new starts; in-flight drags continue) and delegates per-type state:
- `WorkerDragHandler` — `pendingTokenId`, `active`, `scaleMode`, `scaleTokenId`, `clickedNearPerimeter`.
- `PlantDragHandler` — `pendingPlantId`, `active`, `arcHandle`, `radiusHandle`, `radiusPreview`.
- `AreaDragHandler` — `pendingAreaId`, `active`, `areaCentroid`, `pendingTempVertexIndex`.
- `RoadDragHandler` — `pendingRoadId`, `active`, `roadCentroid`.

Invariant: `readOnly || isAnyDragActive()` ⟂ new drag start.

`DragContext` maintains:
- `dragBeaconRafId` / `pendingDragBeaconUpdate` — throttles beacon updates to one RAF.
- `cachedDragFeatures` / `cachedDragEntityIndex` — full feature array cached once, mutated in-place thereafter.
- `touchDragFeature` — single cached GeoJSON feature for lightweight touch overlay.

### Vertex editing
`MapVertexEditController` maintains:
- `dragState` — `active`, `startPos`, `startCoords`, `vertexIndex`.
- `boxState` — `active`, `startLngLat`, `currentLngLat`.
- `lassoState` — `active`, `points`.
- `justDragged` — suppresses click processing after drag end.
- `attached` — whether listeners are bound.

### Context menu FSM
`MapContextMenuController` maintains:
- `rightClickStart` / `rightClickWasDrag` — rotation-vs-menu discrimination.
- `suppressMapClickUntil` — timestamp to swallow synthetic click after long-press.

`MapContextMenuComponent` (signals):
- `mainMenu`, `entityMenu`, `layerMenu`, `disambiguation`, `coordsPopup` — nullable signal states.
- `createSubmenuOpen`, `layerTypeSubmenuOpen` — signal-driven submenu expansion.
- `editingDisabled` — drives visual disable for mutating menu items; fed by the read-only predicate stream.
- `containerHeight` — fed by `ResizeObserver` for flip-up calculations.

### Selection tools
`MapSelectionToolsController` maintains:
- `currentTool` — `'none' | 'box' | 'lasso'`.
- `boxState` — `active`, `startPixel`, `currentPixel`.
- `lassoState` — `active`, `points`.

### Touch adapter
`MapTouchAdapter` maintains:
- `longPressTimer` / `longPressTriggered` — 500 ms context-menu timer.
- `touchStartPos` — for movement-threshold cancellation.
- `entityDragActive` — true while touch drag is in progress.

### Middle pan
`MapMiddlePanController` maintains:
- `isPanning` / `lastPos` — pan state and last mouse position.
- `originalCursor` — restored on mouseup.

### Event bus
`MapInteractionService` maintains a single `Subject<MapInteractionEvent>`; all consumers read from `events$`.

## Internals

### Drag lifecycle
All handlers use a two-phase threshold model:
1. `mousedown`/`touchstart` seeds `pending*Id`, `startPos`, `startTime`.
2. `mousemove` exceeds `DRAG_THRESHOLD_PX` (5 px) → `active = true`, disable `dragPan`.
3. `mouseup`/`touchend` commits via callback, re-enables `dragPan`, clears visuals.

`WorkerDragHandler` adds perimeter detection: click in outer 8% of radius (`TOKEN_PERIMETER_THRESHOLD` 0.92) enters `scaleMode` on threshold crossing.

### Clash preview during resize
`WorkerDragHandler::calculatePreviewClashState` builds a Turf circle from preview radius and tests `booleanIntersects` against tokens (red), plant drop zones (red), and areas (amber). Time-range overlap is checked via `TimeUtilityService` to ignore non-overlapping shifts.

### Touch drag optimisation
Touch drags skip threshold and use a lightweight single-feature overlay (`drag-entity` source) instead of rebuilding the full `beacons` source. Ghost circle is static; only overlay coordinate and drag line mutate.

### Vertex edit OT op broadcast
On drag end, `MapVertexEditController` compares `startCoords` to current vertices and emits `onVertexOp` `move` ops. Edge clicks emit `insert` ops. Deletion emits `delete` ops in descending index order to avoid index shifting.

### Context menu disambiguation
`getEntityAtPoint` queries features in priority order: beacons → plant-drag-layer → inactive cranes → POIs → deliveries → roads → geometadata, filtering floor-hidden features. `getAllEntitiesAtPoint` deduplicates for the picker.

`handleRightClickRelease` uses a 5 px distance fallback because MapLibre may not emit mousemove during rotation. Overlapping entities trigger `showDisambiguationIfNeeded` instead of a menu.

### Selection tools Turf.js integration
Box selection creates a screen-aligned rectangle via `unproject` of corners. Tokens and plants are tested with `booleanPointInPolygon`; areas use `booleanIntersects`. Lasso closes the point ring before testing. Both clear the tool on completion.

### Touch adapter gesture recognition
Long-press uses a 500 ms timer cancelled by >10 px movement or multi-touch. Entity drag prefers proximity-based detection (`TOUCH_DRAG_RADIUS_PX` 44 px) against the selected entity's known screen position; fallback `queryRenderedFeatures` bounding-box query handles unselected entities.

### Middle-pan implementation
`MapMiddlePanController` listens on canvas for `mousedown` (button 1) and on `window` for `mousemove`/`mouseup` so panning continues outside the canvas. Calls `map.panBy([-dx, -dy])` with zero duration. Suppresses context menu while panning.

### Event dispatch routing
`MapEventDispatchService` subscribes to `events$` and routes via a ~60-case `switch`. Events needing component-local state (creation host ViewChild, bearing, layer edits) go through `MapEventCallbacks`; everything else dispatches to injected services. `subscribe()` → `registerCallbacks()` must be called first or it logs an error and returns.

## Touches

| resource | how | why |
|---|---|---|
| MapLibre GL | canvas event listeners, source/layer mutation, `queryRenderedFeatures` | map rendering and hit detection |
| Turf.js | `circle`, `booleanIntersects`, `booleanPointInPolygon`, `polygon`, `point` | clash preview, selection intersection tests |
| DOM | `ResizeObserver`, `requestAnimationFrame`, `navigator.vibrate` | menu flip-up, beacon throttling, haptic feedback |

## Gotchas

- `MapDragController.setReadOnly(true)` does **not** cancel in-flight drags — it only blocks new starts.
- `WorkerDragHandler` scale mode and move mode share `mouseup` handlers; be sure `clearDragVisuals()` runs once.
- `PlantDragHandler` inactive cranes live in dedicated sources; plant drag updates both `plants-geojson` and inactive crane sources.
- `MapVertexEditController` labels layer was removed due to Zone.js/MapLibre tile corruption when symbol layers share a source with circle layers.
- `MapContextMenuComponent` uses signals instead of `markForCheck` because MapLibre handlers fire outside Angular's zone; `markForCheck` races under worker contention.
- `computeFeatureContainment` skips `INFRASTRUCTURE_AREA_FEATURE_TYPES` (`building`, `zone`) when enumerating contained areas. Without this filter, selecting a building surfaces overlapping zones and neighbouring buildings as spurious "contents".
- `MapEventDispatchService` must have `registerCallbacks()` called before `subscribe()`; otherwise the subscription silently errors and no events route to component callbacks.
- `MapTouchAdapter` multi-touch (>1 finger) aborts both long-press and entity drag to allow MapLibre pinch-zoom.
