---
trigger: { channel: ui, ref: "map mouse down on entity" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
Left-click (or touchstart) on a draggable map entity: worker beacon, plant, area polygon, road line, or resize/arc/radius handle.

## Steps
1. `map/map-event-wiring.ts::MapEventWiring` detects mousedown on draggable layers and dispatches to `map/map-drag.ts::MapDragController`.
2. `MapDragController::shouldBlockStart()` gates on `readOnly || isAnyDragActive()`; if clear, delegates to the entity-type handler.
3. `map/map-drag-worker.ts::WorkerDragHandler::startTokenDrag` seeds `pendingTokenId`, records `startPos`, and computes `clickedNearPerimeter` (`clickDistPx > radiusPx * TOKEN_PERIMETER_THRESHOLD`).
4. `WorkerDragHandler::startResizeHandleDrag` enters `scaleMode` immediately (no threshold).
5. `map/map-drag-plant.ts::PlantDragHandler::startPlantDrag` seeds `pendingPlantId` and records `startPos`.
6. `PlantDragHandler::startArcHandleDrag` or `startRadiusHandleDrag` enters arc/radius mode immediately.
7. `map/map-drag-area.ts::AreaDragHandler::startAreaDrag` seeds `pendingAreaId`, resolves `areaCentroid`, and checks `canDragArea` and locked state.
8. `map/map-drag-road.ts::RoadDragHandler::startRoadDrag` seeds `pendingRoadId` and computes `roadCentroid`.
9. Mousemove handlers (`onTokenDragCheck`, `onPlantDragCheck`, etc.) measure screen distance against `map/map-drag-types.ts::DRAG_THRESHOLD_PX` (5 px).
10. Below threshold → no-op; above threshold → `active = true`, `dragPan.disable()`, cursor changes, and live visual updates begin.
11. Worker threshold crossing with `clickedNearPerimeter === true` → switches from pending move to `scaleMode` (`onTokenScale` handler).
12. During worker scale drag, `WorkerDragHandler::calculatePreviewClashState` builds a Turf circle and tests `booleanIntersects` against tokens (red), plant drop zones (red), and areas (amber), gated by `doTimeRangesOverlap`.
13. Live drag visuals mutate GeoJSON sources directly via `map/map-drag-types.ts::DragContext`: `drag-ghost`, `drag-line`, `resize-indicator`, `arc-dial`, `crane-dropzones`, and beacons (throttled to one RAF).
14. Ephemeral broadcasts: each `mousemove` calls `DragCallbacks::onEphemeralPosition` (or radius/arc variants), which routes through `MapComponent` callbacks to `map/map-ephemeral-position-throttler.ts::EphemeralPositionThrottler::send`.
15. `EphemeralPositionThrottler` throttles outbound messages to one per 100 ms and calls `services/websocket.service.ts::WebSocketService::sendEphemeralPosition` (or `sendEphemeralTokenRadius`, `sendEphemeralPlantRadius`, `sendEphemeralPlantArc`).
16. Inbound ephemeral events from other clients are received by `WebSocketService`, routed to `EphemeralPositionThrottler`, which mutates the local entity array in place and repaints beacons/plants.
17. Touch path: `map/map-touch-adapter.ts::MapTouchAdapter::onTouchStart` → `TouchAdapterCallbacks::onEntityTouchDragStart` → `MapDragController::startTouchDrag`, which delegates to the handler's `startTouchDrag`.
18. Touch skips threshold and uses a lightweight single-feature `drag-entity` overlay (`DragContext::startTouchDragOverlay`) instead of rebuilding the full beacons source.
19. Mouseup/touchend clears `mousemove` listeners, re-enables `dragPan`, and computes final geometry.
20. Worker move end → `DragCallbacks::onTokenMoved` → `services/map-interaction.service.ts::MapInteractionService` emits `token:moved`.
21. Worker resize end → `DragCallbacks::onTokenRadiusScaled` → `token:radiusScaled`.
22. Plant move end → `DragCallbacks::onPlantMoved` → `plant:moved`.
23. Plant radius end → `DragCallbacks::onPlantRadiusChanged` → `plant:radiusChanged`.
24. Plant arc end → `DragCallbacks::onArcChanged` → `plant:arcChanged`.
25. Area move end → `DragCallbacks::onAreaMoved` → `area:moved`.
26. Road move end → `DragCallbacks::onRoadMoved` → `road:moved`.
27. `services/map-event-dispatch.service.ts::MapEventDispatchService` routes events to services:
   - `token:moved` → `EntityMoveService::onTokenMoved` → `WorkerHandler::moveWorker` → `EntityService::updateToken` (simple moves debounce through `EntityMoveService::updateTokenPosition`) → `ApiService::patchToken`.
   - `token:radiusScaled` → `EntityMoveService::onTokenRadiusScaled` → `WorkerHandler::scaleRadius` → `EntityMoveService::updateTokenPosition` (debounced 400 ms) → `EntityService::updateToken` → `ApiService::patchToken`.
   - `plant:moved` → `EntityMoveService::onPlantMoved` → `PlantHandler::movePlant` → `EntityService::updatePlant` → `ApiService::updatePlant`.
   - `plant:radiusChanged` → `EntityMoveService::onPlantRadiusChanged` → `PlantHandler::updateRadius` → `EntityService::updatePlant` → `ApiService::updatePlant`.
   - `plant:arcChanged` → `EntityMoveService::onPlantArcChanged` → `PlantHandler::updateArc` → `EntityService::updatePlant` → `ApiService::updatePlant`.
   - `area:moved` → `AreaFeatureInteractionService::onAreaMoved` → `AreaHandler::moveArea` → `EntityService::updateArea` → `ApiService::updateArea`.
   - `road:moved` → `EntityMoveService::onRoadMoved` → `RoadHandler::updateRoad` → `ApiService::updateRoad`.
28. On HTTP success, the handler updates local state (`EntityService` stores or `RoadEditorStateService`), which emits to downstream subscribers.
29. The backend broadcasts `entity_updated` over the WebSocket room.
30. `services/websocket-event-router.service.ts::WebSocketEventRouterService` receives `entity_updated` and calls `EntityService::wsUpdateToken`, `wsUpdatePlant`, or `wsUpdateArea`.
31. `EntityService` suppresses WebSocket updates for entities with pending optimistic updates (`_pendingOptimistic`).
32. Store emissions flow through `FilteredEntityCacheService` to `MapComponent`, which sets dirty flags and schedules a single RAF flush.
33. `MapComponent` updates the relevant GeoJSON sources (`updateBeacons`, `updatePlantSource`, `updateGeometadataSource`, `updateRoadsSource`).

## Side effects
- MapLibre `dragPan` disabled/enabled around active drag.
- GeoJSON source mutations: `drag-ghost`, `drag-line`, `drag-entity`, `resize-indicator`, `arc-dial`, `crane-dropzones`, `beacons`, `plants-geojson`, `geometadata`, `roads-geojson`.
- HTTP PATCH/PUT to backend (`/tokens/{id}`, `/plants/{id}`, `/areas/{id}`, `/roads/{id}`).
- WebSocket ephemeral broadcasts during drag (`ephemeral_position`, `ephemeral_token_radius`, `ephemeral_plant_radius`, `ephemeral_plant_arc`).
- WebSocket `entity_updated` broadcast after commit.
- Optimistic local state updates in `EntityService` stores.
- Undo snapshots recorded in `UndoExecutorHandler`.

## Failure modes
- `MapDragController.setReadOnly(true)` does **not** cancel in-flight drags — it only blocks new starts via `shouldBlockStart()`.
- Worker scale mode and move mode share `mouseup` handlers; `clearDragVisuals()` must run once to avoid leaking ghost features.
- Plant drag updates both `plants-geojson` and inactive crane sources (`updateInactiveCraneSourceWithDrag`); missing the inactive source leaves a stale footprint.
- Touch multi-touch (>1 finger) aborts drag to allow MapLibre pinch-zoom; `entityDragActive` is cleared and `dragPan` re-enabled.
- Token simple moves (no building transition) use a debounced pipeline (`EntityMoveService::tokenUpdateSubject` 400 ms); rapid successive drags on the same token coalesce into one HTTP call.
- WebSocket inbound `entity_updated` is suppressed for entities with pending optimistic updates to prevent the server's stale state from overwriting the optimistic drag position.
- Area drag inside a multi-level building returns `needs_level_selection` without persisting; the user must confirm a floor via the level-selector modal before `completeMoveAreaWithLevel` issues the API call.
