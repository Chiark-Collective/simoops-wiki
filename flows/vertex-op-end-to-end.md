---
trigger: { channel: ui, ref: "MapVertexEditController interaction (drag, insert, delete)" }
services: [ui, backend]
contracts: [ui-backend/websocket-contract]
external: []
---

## Trigger
User clicks "Edit shape" and then drags, inserts, or deletes a vertex in area/road vertex-edit mode.

## Steps
1. User clicks "Edit shape" on an area or road.
   `map/map.component.ts::startVertexEdit` guards with `RevisionModeService.guardEdit`.
2. `map/map.component.ts::startVertexEdit` checks `dataLockService.isEntityLocked`.
3. `services/vertex-edit.service.ts::startEditing` deep-copies current vertices.
4. `services/vertex-edit.service.ts::startEditing` clears undo and redo stacks.
5. `services/vertex-edit.service.ts::startEditing` resets `_currentRev` to the feature's current geometry revision.
6. `services/vertex-edit.service.ts::startEditing` emits `enabled = true`.
7. `map/map.component.ts::initVertexEditController` wires `VertexEditCallbacks`.
8. `map/map.component.ts::initVertexEditController` instantiates `MapVertexEditController`.
9. `map/map-vertex-edit.ts::MapVertexEditController.attach` binds mouse, touch, and map move listeners.
10. `map/map-vertex-edit.ts::MapVertexEditController.attach` calls `updateSources`.
11. `map/map-vertex-edit.ts::updateSources` refreshes GeoJSON sources `vertex-edit-vertices`, `vertex-edit-edges`, `vertex-edit-polygon`, `vertex-edit-selection`.
12. Click on vertex: `onMouseDown` selects immediately.
13. Shift+click in `onClick` toggles selection via `VertexEditService.toggleVertexSelection`.
14. Alt+drag or Ctrl+drag: `startBoxSelect` / `startLassoSelect` → `findVerticesInBox` / `findVerticesInPolygon` → `selectVertices`.
15. Edge click: `findEdgeAtPoint` → `VertexEditService.addVertex` emits `insert` op via `onVertexOp`.
16. Vertex drag: `onMouseDown` seeds `dragState.startCoords`.
17. `onMouseMove` exceeds `DRAG_THRESHOLD_PX` → `dragState.active = true`; `moveVertex` updates live.
18. Drag end: `onMouseUp` compares `startCoords` to current vertices and emits `move` ops via `onVertexOp`.
19. `VertexEditService.endDrag` commits `preDragSnapshot` to undo stack if vertices changed.
20. Delete: `deleteSelectedVertices` emits `delete` ops in descending index order via `onVertexOp`.
21. `VertexEditService.deleteSelectedVertices` enforces minimum vertices (roads ≥2, polygons ≥3).
22. `map/map.component.ts::onVertexOp` calls `WebSocketService.sendVertexOp(featureId, op, baseRev)`.
23. `WebSocketService.sendVertexOp` attaches local `_currentRev` as `baseRev`.
24. Frontend optimistically updates live GeoJSON sources via `VertexEditService` move/insert/delete.
25. `WebSocketService` transmits `action: "vertex_op"` over the WebSocket room.
    The payload includes `feature_id`, `base_rev`, and the op payload. [WebSocket contract](../contracts/ui-backend/websocket-contract.md)
26. `websocket.py::_handle_vertex_op` receives the message.
27. `websocket.py::_handle_vertex_op` requires an active room subscription.
28. Handler parses `feature_id`, `op_type`, `base_rev`, `expected_geom_rev`.
29. Loads feature from PostGIS.
30. Verifies RBAC with `Permission.entity_edit`.
31. Validates geometry revision gate (`expected_geom_rev` vs current).
32. `vertex_op_service.py::VertexOpService.handle_vertex_op` delegates to `vertex_op_store.py::transform_and_record`. [backend sequence](../services/backend/flows/vertex_op_flow.md)
33. `vertex_op_store.py` transforms the incoming op against concurrent missed ops using OT.
    Transformation rewrites indices to account for insertions and deletions that arrived in the meantime.
34. `vertex_op_buffer.py` fixed-size ring buffer supplies recent op history.
35. If the ring buffer cannot cover the revision gap, transformation fails.
36. Transformed op applied to the feature's exterior ring.
37. Resulting geometry validated via `polygon_from_lonlat`.
38. Valid geometry persisted to PostGIS.
    `geometry_revision` is incremented implicitly by the update.
39. `audit_service.py::AuditService.record` writes an audit entry.
    The entry captures the geometry change summary.
40. `websocket_runtime::ws_manager.broadcast_ephemeral` emits `vertex_op_applied`.
    All room subscribers except the original sender receive the event.
41. `entity_broadcast.py::broadcast_entity_event` emits `entity_updated`.
    The sequenced broadcast carries the new geometry to all clients.
42. Original sender receives `vertex_op_ack` with new `rev` and `polygon_wgs84`.
43. `map/map-subscription-orchestrator.ts::subscribeToVertexOps` receives `vertex_op_applied`.
44. `services/vertex-edit.service.ts::applyRemoteVertexOp` applies authoritative `polygon_wgs84`.
    Local optimistic state is overwritten by the server geometry.
    Selection indices are remapped to match the new vertex order.
45. `applyRemoteVertexOp` adjusts local selection indices and metadata.
46. `applyRemoteVertexOp` updates `_currentRev`.
47. `applyRemoteVertexOp` deliberately skips the undo stack.
48. `applyRemoteVertexOp` drops any local selection whose vertex was deleted remotely.
49. `VertexEditService` undo/redo stacks are session-scoped; new edit session clears both.
50. `services/road-editor-state.service.ts::wsUpdateRoad` keeps local road list consistent with remote broadcasts.
51. Save: `MapVertexEditController.save` runs `@turf/kinks` self-intersection check.
52. Save: `MapVertexEditController.save` enforces minimum vertex counts (polygons ≥3, roads ≥2).
53. Save: `MapVertexEditController.save` calls `VertexEditService.validate` to preview errors.
54. `MapVertexEditController.save` emits `vertexEdit:saved` or `vertexEdit:roadSaved`.
55. `services/map-event-dispatch.service.ts` routes saved event.
56. `services/area-feature-interaction.service.ts::onVertexEditSaved` handles area save.
57. `onVertexEditSaved` calls `EntityService.updateArea` → HTTP PATCH `/areas/{id}`.
    `EntityService.updateArea` delegates to `GeometadataService.updateFeature` for geometry persistence.
58. `services/area-feature-interaction.service.ts::onRoadVertexEditSaved` handles road save.
59. `onRoadVertexEditSaved` calls `ApiService.updateRoad` → HTTP PATCH `/roads/{id}`.
    Road geometry is saved and `RoadEditorStateService` updated.
60. `EntityEditSessionService` constructor subscribes to `entity_deleted` independently to avoid circular dependency.
61. Cancel: `MapVertexEditController.cancel` calls `VertexEditService.cancelEditing`.
62. `VertexEditService.cancelEditing` restores `originalVertices`.
63. `MapVertexEditController.cancel` emits `vertexEdit:cancelled`. [frontend journey](../services/ui/flows/polygon-vertex-edit.md)
64. `MapVertexEditController.detach` cleans up all listeners and sources on save or cancel.
65. `WebSocketService` sends periodic `ping` every 30s; missed pongs trigger reconnect and `catch_up`.

## Side effects
- MapLibre GL source mutations (`vertex-edit-vertices`, `vertex-edit-edges`, `vertex-edit-polygon`, `vertex-edit-selection`).
- `VertexEditService._state` mutations: live vertex arrays, `_currentRev`, selection set.
- `VertexEditService` undo/redo stack mutations (local only, cleared on new session).
- `dragState` mutations in `MapVertexEditController` during active drag.
- `preDragSnapshot` captured and pushed to undo stack on drag end.
- Selection set mutations in `VertexEditService` (toggle, box, lasso).
- WebSocket `vertex_op` message sent to backend; `vertex_op_applied` broadcast and `vertex_op_ack` returned.
- PostGIS UPDATE of `GeometadataFeature.geometry` and implicit `geometry_revision` bump.
- Audit log INSERT with geometry change summary.
- Redis ephemeral broadcast of `vertex_op_applied`.
- Sequenced `entity_updated` broadcast via `entity_broadcast.py`.
- HTTP PATCH/PUT to `/areas/{id}` or `/roads/{id}` on save.
- `MapInteractionEvent` emissions (`vertexEdit:saved`, `vertexEdit:roadSaved`, `vertexEdit:cancelled`, `vertexEdit:message`).
- `RoadEditorStateService._state` mutation on road save.
- `GeometryService` recalculates bounding box on save.
- `ClashStateService` may re-evaluate clashes after `entity_updated`.
- `GeometadataService` cache invalidation on geometry update.
- `MapVertexEditController.detach` removes listeners and GeoJSON sources.
- `EntityEditSessionService` tears down state on `entity_deleted`.
- `EntityService` emits `entity_updated` to WebSocket layer on HTTP save.
- `WebSocketService` heartbeat `ping` every 30s keeps connection alive during long edit sessions.

## Failure modes
- Data-locked entity: `guardEdit` or `dataLockService.isEntityLocked` blocks entry; error toast shown.
- Self-intersecting polygon: `@turf/kinks` detects kinks; save rejected with toast.
- Too few vertices: delete rejected if remaining < 3 (polygons) or < 2 (roads); toast error.
- Drag threshold not met: no-op, no op emitted.
- Empty selection delete: no-op.
- Box/lasso select with no vertices inside: no state change.
- Stale revision: `base_rev` too old or gap > max_ops → `vertex_op_ack` with `stale: true`; client reloads geometry.
- Geometry revision mismatch: `expected_geom_rev != current_geom_rev` → `vertex_op_ack` with `stale: true`.
- OT CAS contention: Redis Lua CAS returns -1 after 5 retries → `RuntimeError` logged; client generic error.
- Invalid polygon after transform: < 3 vertices or self-intersection → `vertex_op_ack` with error.
- Forbidden: missing `entity_edit` or global feature → `vertex_op_ack` with `reason: forbidden`.
- Feature not found: missing `GeometadataFeature` row → `vertex_op_ack` with `reason: feature_not_found`.
- WS disconnect during edit: `sendVertexOp` queued or lost; local edits persist but remote users stale until reconnect.
- Auth error on save: HTTP 401/403; message suppressed for auth errors.
- Optimistic update conflict: local op and remote op race; authoritative `vertex_op_applied` overwrites local state.
- HTTP save conflict: 409 if geometry changed on server between WS op and HTTP PATCH; client may need reload.
- Ring buffer eviction: high-frequency multi-user edits may evict ops from `vertex_op_buffer.py` before persistence, causing stale-revision cascades.
- Local selection loss: `applyRemoteVertexOp` preserves indices across insert/delete, but if locally selected vertex is deleted remotely it is dropped.
- OT edge case: concurrent `move` + `delete` on same vertex may produce unexpected geometry in `vertex_op.py`.
- Remote op on wrong feature: `applyRemoteVertexOp` no-ops if `featureId` mismatch.
- RBAC revocation mid-session: subsequent ops rejected with `vertex_op_ack` forbidden.
- PostGIS deadlock: rare, retry logic in service layer may abort the op.
- Audit log write failure: non-blocking, logged but does not fail the request.
- Save while disconnected: HTTP PATCH queued or fails; user sees error toast.
- Concurrent HTTP save: two users save same feature; last-write-wins on HTTP layer.
- Missing `baseRev`: frontend sends op without revision → backend rejects as stale.
- Memory pressure: large polygons with many vertices may strain `vertex_op_buffer.py`.
- Client memory leak: `MapVertexEditController` not detached on rapid navigation → orphaned listeners.
- Backend `vertex_op.py` transform returns no-op for redundant move.
- Heartbeat timeout: 3 missed pongs → reconnect; ephemeral ops in flight may be lost.
- `catch_up` after reconnect may deliver stale `vertex_op_applied` events; frontend deduplicates by `rev`.
