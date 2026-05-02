---
service: ui
summary: Entity edit session, form initializers, save handlers, modal dispatch, and vertex editing.
paths:
  - src/app/services/entity-edit-orchestrator.service.ts
  - src/app/services/entity-edit-session.service.ts
  - src/app/services/edit-form-initializer.ts
  - src/app/services/edit-save.handler.ts
  - src/app/services/entity-modal-orchestrator.service.ts
  - src/app/services/modal-result-dispatch.service.ts
  - src/app/services/modal-result-entity-crud.service.ts
  - src/app/services/modal-result-data-lock.service.ts
  - src/app/services/modal-result-road-edit.service.ts
  - src/app/services/modal-result-geometadata.service.ts
  - src/app/services/road-editor-state.service.ts
  - src/app/services/vertex-edit.service.ts
  - src/app/dashboard/properties-panel/properties-panel.component.ts
flows: []
touches:
  - http
  - websocket
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Manages the full entity-edit lifecycle from modal open through save. `EntityEditSessionService` tracks the active session with dirty-field preservation and live WebSocket merge. `VertexEditService` provides polygon and road vertex manipulation with undo/redo and OT revision tracking.

## Interface
- `services/entity-edit-orchestrator.service.ts::EntityEditOrchestrator` — Opens edit modals for tokens, plants, and areas; routes schedule-aware saves and records undo.
- `services/entity-edit-session.service.ts::EntityEditSessionService` — Session lifecycle, data-lock gating, live WS merge, dirty-field tracking, schedule occurrence fetching, and cancel cleanup.
- `services/edit-form-initializer.ts::EditFormInitializer` — Stateless conversion of `Worker`, `Plant`, and `Area` snapshots into `EntityEditForm` objects.
- `services/edit-save.handler.ts::EditSaveHandler` — Stateless save dispatcher delegating to `WorkerHandler`, `PlantHandler`, and `AreaHandler`; handles contractor reassignment.
- `services/entity-modal-orchestrator.service.ts::EntityModalOrchestrator` — Facade composing edit and delete orchestrators; registers dashboard callbacks and handles context-menu edit/delete requests.
- `services/modal-result-dispatch.service.ts::ModalResultDispatchService` — Coordinates all modal-result handler subscriptions.
- `services/modal-result-entity-crud.service.ts::ModalResultEntityCrudHandler` — Persists delivery, PoI, text label, and alert edits from modal results.
- `services/modal-result-data-lock.service.ts::ModalResultDataLockHandler` — Applies data-lock set/clear operations from modal results.
- `services/modal-result-road-edit.service.ts::ModalResultRoadEditHandler` — Saves road edits and delegates road deletes.
- `services/modal-result-geometadata.service.ts::ModalResultGeometadataHandler` — Building edits, layer updates, and geometadata feature selection.
- `services/road-editor-state.service.ts::RoadEditorStateService` — Reactive state for road drawing mode, selection, vertex manipulation, and WebSocket sync.
- `services/vertex-edit.service.ts::VertexEditService` — Polygon and road vertex editing with selection, drag, add, delete, undo/redo, validation, and OT revision tracking.
- `dashboard/properties-panel/properties-panel.component.ts::PropertiesPanelComponent` — Right-side panel showing selected entity details, clashes, audit info, and inline field edits.

## State
- `EntityEditSessionService` holds a single `EditSession` in `_session` (BehaviorSubject). Fields: `entityType`, `entityId`, `entity`, `isNewPlacement`, `buildingLevels`, `auditInfo`, `scheduleOccurrences`, `dirtyFields: Set<string>`.
  - Invariant: `dirtyFields` is preserved across live WS `entity_updated` merges → user changes are not overwritten by remote updates.
  - `wsSessionSub` stores the active WebSocket subscription for the editing entity.
- `RoadEditorStateService` holds `RoadEditorState` in `_state` (BehaviorSubject). Fields: `mode: RoadEditorMode`, `roads: Road[]`, `selectedRoadId: string | null`, `drawState: RoadDrawState`, `loading: boolean`.
  - Invariant: `mode === 'drawing'` ⟂ `selectedRoadId !== null`.
- `VertexEditService` holds `VertexEditState` in `_state` (BehaviorSubject). Fields: `enabled`, `featureId`, `featureType`, `vertices`, `vertexMetadata`, `selectedIndices`, `selectionMode`, `isDragging`, `isDirty`, `originalVertices`, `originalMetadata`.
  - Undo/redo stacks (`undoStack`, `redoStack`) capped at `MAX_UNDO_DEPTH` (50).
  - `preDragSnapshot` captured at drag start; committed to undo stack on `endDrag` only if vertices changed.
  - `_currentRev` tracks OT revision for concurrent vertex operations.
  - Invariant: `enabled === false` → `undoStack.length === 0 && redoStack.length === 0`.
- `ModalResultDispatchService` tracks `started` boolean to prevent double subscription.
- `PropertiesPanelComponent` caches `clashLookups`, `entityClashVms`, `containedClashVms`, `intersections`, `containment`, and a `userMap` for audit name resolution. Inline edit state: `editingField`, `editValue`.

## Internals
- `EntityEditOrchestrator` guards edits with `RevisionModeService.guardEdit` before opening any modal.
- Open flow: `openTokenEditModal` / `openPlantEditModal` / `openAreaEditModal` → `EntityEditSessionService.openTokenEdit` etc. → returns `EntityEditForm` → dashboard callback `setEditForm` binds it to the modal.
- `EntityEditSessionService.openEditSession` creates the session, starts presence tracking, subscribes to live WS updates, opens the modal, and fetches schedule occurrences asynchronously.
- Live WS merge: `subscribeToLiveUpdates` listens to `entity_updated` for the session `entityId` and replaces `session.entity` with the broadcast payload. Dirty fields are not cleared.
- Schedule occurrence fetch: `fetchScheduleOccurrencesIfNeeded` calls the schedule group API, reverse-maps sibling `start_at`/`end_at` to `ScheduleOccurrence` objects using site shifts, and updates the session.
- Save flow: `EntityEditOrchestrator.confirmEditModal` → `routeScheduleEdit` (batch create, reconcile, convert, group edit) or `saveSingleEntity` → `EntityEditSessionService.save` → `EditSaveHandler.save`.
- `EditSaveHandler.save` branches by `entityType`:
  - `worker` → `WorkerHandler.editWorker`; if contractor changed on a new placement, `recreateTokenWithNewContractor` deletes the old token and creates a new one because the API does not support `contractor_id` mutation.
  - `plant` → `PlantHandler.editPlant`.
  - `area` → `AreaHandler.editArea`.
- `EntityEditSessionService.cancel` closes the session; for new placements it deletes the entity via `deleteToken`/`deletePlant`.
- Modal result dispatch: `ModalResultDispatchService.subscribe` starts all handlers once. Each handler listens to `ModalResultService` result tokens and calls domain services.
  - `ModalResultEntityCrudHandler` handles delivery, PoI, text label, and alert CRUD.
  - `ModalResultDataLockHandler` calls `DataLockService.setDataLock` for set/clear.
  - `ModalResultRoadEditHandler` delegates saves to `RoadHandler.updateRoad` and deletes to `EntityModalOrchestrator.deleteRoad`.
  - `ModalResultGeometadataHandler` persists building edits via `GeometadataService.updateFeature`.
- `RoadEditorStateService` WS sync methods (`wsAddRoad`, `wsUpdateRoad`, `wsRemoveRoad`) are called by the WebSocket layer to keep the local road list consistent with the server.
- `VertexEditService` validation uses `@turf/kinks` to detect self-intersection for polygons; roads require ≥2 vertices, polygons ≥3.
- `VertexEditService.applyRemoteVertexOp` handles concurrent remote vertex ops without pushing to the undo stack. It adjusts `selectedIndices` and `vertexMetadata` for insert/delete and updates `_currentRev`.
- `PropertiesPanelComponent` recomputes clash view models, intersections, and containment in `ngOnChanges` to keep template bindings stable under `OnPush`. Audit names are resolved via bulk user API (`ApiService.getUsersBulk`).

## Touches
| resource | how | why |
|---|---|---|
| HTTP | `ApiService`, `AuditApi`, `DataLockService`, domain handlers | Fetch entity data, save edits, load audit history, set data locks |
| WebSocket | `WebSocketService.events$` | Live entity updates during edit session, remote road add/update/remove, remote vertex operations |

## Gotchas
- `EntityEditOrchestrator.saveSingleEntity` does NOT call `loadTokens()` or `loadPlant()` after save because `loadTokens` uses `selectedShift`, which would erase cross-shift tokens. Clash color updates arrive via WebSocket.
- `EditSaveHandler.recreateTokenWithNewContractor` performs a delete-then-create because the backend API disallows direct `contractor_id` changes on existing workers.
- `EntityEditSessionService.fetchBuildingLevelsIfNeeded` returns a placeholder level immediately and updates the session asynchronously after the API call; the modal may see a brief stale label.
- `PropertiesPanelComponent` uses `entityType === 'area'` for the audit API even when the selection is a `GeometadataFeature` (building), because the backend audit endpoint expects `'area'` as the umbrella type.
- `VertexEditService` undo/redo is per-session; starting a new edit session clears both stacks.
- `VertexEditService.applyRemoteVertexOp` preserves local selection indices across insert/delete, but if the locally selected vertex is deleted remotely it is dropped from the selection.
- `RoadEditorStateService.selectRoad` is ignored while `mode === 'drawing'` to prevent accidental selection during draw.
- `EntityEditSessionService` constructor subscribes to `entity_deleted` and `schedule_group_deleted` WS events independently of `WebSocketEventRouterService` to avoid a circular dependency.
