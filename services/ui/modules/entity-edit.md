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
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Manages the full edit lifecycle: opening a modal, initialising form state from entity snapshots, saving changes through per-kind handlers, and handling modal results. `EntityEditSessionService` tracks the active session with dirty-field and live WebSocket merge support. `VertexEditService` provides polygon and road vertex manipulation with undo/redo.

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
