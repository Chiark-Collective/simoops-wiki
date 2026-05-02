---
trigger: { channel: ui, ref: "area vertex edit mode" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User clicks "Edit shape" on an area or road from the properties panel or context menu.

## Steps
1. `map/map.component.ts::startVertexEdit` or `startRoadVertexEdit` guards with `RevisionModeService.guardEdit` and data-lock checks.
2. `services/vertex-edit.service.ts::startEditing` or `startRoadEditing` deep-copies vertices, clears undo/redo stacks, resets `_currentRev`, and emits `enabled = true`.
3. `map/map.component.ts::initVertexEditController` wires `VertexEditCallbacks` and instantiates `MapVertexEditController`.
4. `map/map-vertex-edit.ts::MapVertexEditController.attach` binds mouse/touch/map listeners and calls `updateSources`.
5. `map/map-vertex-edit.ts::updateSources` refreshes GeoJSON sources `vertex-edit-vertices`, `vertex-edit-edges`, `vertex-edit-polygon`, and `vertex-edit-selection`.
6. Click on vertex: `onMouseDown` selects immediately; Shift+click in `onClick` toggles selection via `VertexEditService.toggleVertexSelection`.
7. Alt+drag or Ctrl+drag: `startBoxSelect` / `startLassoSelect` → `findVerticesInBox` / `findVerticesInPolygon` → `selectVertices`.
8. Edge click: `findEdgeAtPoint` → `VertexEditService.addVertex` inserts vertex; `onVertexOp` emits `insert` op.
9. Vertex drag: `onMouseDown` seeds `dragState.startCoords`; `onMouseMove` exceeds `DRAG_THRESHOLD_PX` → `dragState.active = true`; `moveVertex` updates live.
10. Drag end: `onMouseUp` compares `startCoords` to current vertices and emits `move` ops via `onVertexOp`; `VertexEditService.endDrag` commits `preDragSnapshot` to undo stack if changed.
11. Delete: `deleteSelectedVertices` emits `delete` ops in descending index order; `VertexEditService.deleteSelectedVertices` enforces min vertices (roads ≥2, polygons ≥3).
12. `map/map.component.ts::onVertexOp` calls `WebSocketService.sendVertexOp` with `baseRev`.
13. Backend transforms op against concurrent edits and broadcasts `vertex_op_applied`.
14. `map/map-subscription-orchestrator.ts::subscribeToVertexOps` receives broadcast and calls `VertexEditService.applyRemoteVertexOp`.
15. `services/vertex-edit.service.ts::applyRemoteVertexOp` applies authoritative `polygon_wgs84`, adjusts selection/metadata, updates `_currentRev`, skips undo stack.
16. `services/vertex-edit.service.ts::validate` runs `@turf/kinks` for self-intersection and enforces minimum vertex counts.
17. Save: `MapVertexEditController.save` validates, then `onSave` emits `vertexEdit:saved` or `vertexEdit:roadSaved`.
18. `services/map-event-dispatch.service.ts` routes saved event to `services/area-feature-interaction.service.ts::onVertexEditSaved` or `onRoadVertexEditSaved`.
19. `onVertexEditSaved` calls `EntityService.updateArea` or `GeometadataService.updateFeature` over HTTP.
20. `onRoadVertexEditSaved` calls `ApiService.updateRoad` and updates `RoadEditorStateService`.
21. Cancel: `MapVertexEditController.cancel` restores `originalVertices` via `VertexEditService.cancelEditing` and emits `vertexEdit:cancelled`.
22. `services/road-editor-state.service.ts::wsUpdateRoad` / `wsAddRoad` / `wsRemoveRoad` keep local road list consistent with remote WS broadcasts.

## Side effects
- MapLibre GL source mutations (`vertex-edit-vertices`, `vertex-edit-edges`, `vertex-edit-polygon`, `vertex-edit-selection`).
- `MapInteractionEvent` emissions (`vertexEdit:saved`, `vertexEdit:roadSaved`, `vertexEdit:cancelled`, `vertexEdit:message`).
- WebSocket `vertex_op` messages sent and received.
- HTTP PATCH/PUT to `/areas/{id}` or `/roads/{id}` on save.
- `VertexEditService._state` and `RoadEditorStateService._state` mutations.

## Failure modes
- Data-locked entity: `guardEdit` or `dataLockService.isEntityLocked` blocks entry; error toast shown.
- Self-intersecting polygon: `@turf/kinks` detects kinks; save rejected with toast.
- Too few vertices: delete rejected if remaining < 3 (polygons) or < 2 (roads); toast error.
- Remote op on wrong feature: `applyRemoteVertexOp` no-ops if `featureId` mismatch.
- WS disconnect during edit: `sendVertexOp` queued or lost; local edits persist but remote users stale until reconnect.
- Auth error on save: HTTP 401/403; message suppressed for auth errors.
