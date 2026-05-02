---
trigger: { channel: ui, ref: "entity edit request" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User selects an entity and initiates edit via keyboard, context menu, or properties panel.

## Steps
1. `services/entity-interaction-orchestrator.service.ts::EntityInteractionOrchestrator.selectTokenFromList`, `selectPlantFromList`, or `services/area-feature-interaction.service.ts::AreaFeatureInteractionService.selectArea` sets the active selection.
2. Context menu edit → `services/entity-modal-orchestrator.service.ts::EntityModalOrchestrator.onEntityEditRequested`; keyboard "E" → `dashboard/dashboard-keyboard.service.ts::DashboardKeyboardService.handleEditKey` → facade `openTokenEditModal` / `openPlantEditModal` / `openActiveFeatureEditModal`.
3. Facade delegates to `services/entity-edit-orchestrator.service.ts::EntityEditOrchestrator.openTokenEditModal`, `openPlantEditModal`, `openAreaEditModal`.
4. `EntityEditOrchestrator.revisionGuardTripped` → `services/revision-mode.service.ts::RevisionModeService.guardEdit`; if tripped, flow stops.
5. `EntityEditOrchestrator` calls `services/entity-edit-session.service.ts::EntityEditSessionService.openTokenEdit`, `openPlantEdit`, `openAreaEdit`, each routing to private `openEditSession`.
6. `openEditSession` creates an `EditSession` with `dirtyFields: new Set()`, calls `PresenceService.startEditing`, `subscribeToLiveUpdates`, and `ModalService.openEntityEdit`.
7. `ModalService.openEntityEdit` renders `EntityEditModalComponent`; form initialization via `services/edit-form-initializer.ts::EditFormInitializer.initFormFromToken`, `initFormFromPlant`, or `initFormFromArea`.
8. `EntityEditSessionService.subscribeToLiveUpdates` listens to `wsService.events$` filtered for `event === 'entity_updated'` and matching `entity_id`; merges fresh server data into `session.entity` while preserving `dirtyFields`.
9. `EntityEditModalComponent.onFieldInput` → `EntityEditSessionService.markFieldDirty`, adding the field key to `session.dirtyFields`.
10. `EntityEditModalComponent.onConfirm` emits `(confirm)` bound to dashboard `(confirm)="entityModalOrchestrator.onEditModalConfirm($event)"`.
11. `EntityModalOrchestrator.onEditModalConfirm` → `EntityEditOrchestrator.confirmEditModal` → `saveSingleEntity` → `EntityEditSessionService.save`.
12. `EntityEditSessionService.save` invokes `EditSaveHandler.save`.
13. `EditSaveHandler.save` branches:
    - Worker: `saveToken` → `handlers/worker.handler.ts::WorkerHandler.editWorker`.
    - Plant: `savePlant` → `handlers/plant.handler.ts::PlantHandler.editPlant`.
    - Area: `saveArea` → `handlers/area.handler.ts::AreaHandler.editArea`.
14. Contractor mutation: `EditSaveHandler.saveToken` detects `contractor_id` change → `recreateTokenWithNewContractor` → `EntityService.deleteToken` → `EntityService.createToken` → `EntityService.updateToken`.
15. On success (`result.type === 'saved'` or `'conflict'`), `EntityEditSessionService.save` calls `closeSession`.
16. `closeSession` unsubscribes live WS updates, emits `_session.next(null)`, calls `presenceService.stopEditing`, and `modalService.closeIf('entity-edit')`.
17. Clash color updates arrive asynchronously via WebSocket; `EntityEditOrchestrator.saveSingleEntity` does not eagerly reload tokens.
18. Cancel for new placement: `EntityModalOrchestrator.closeEditModal` → `EntityEditOrchestrator.closeEditModal` → `EntityEditSessionService.cancel`.
19. If `isNewPlacement === true`, `cancel` calls `deleteNewPlacement` → `EntityService.deleteToken` or `EntityService.deletePlant`, then `closeSession`.

## Side effects
- HTTP `PUT/POST/DELETE` to backend entity endpoints.
- WebSocket presence: `PresenceService.startEditing` / `stopEditing`.
- WebSocket subscription to `entity_updated` events.
- `EditSession` state mutation: `dirtyFields`, merged entity data.
- Modal open/close state.
- Token delete-then-create when contractor changes.
- New-placement entity deletion on cancel.

## Failure modes
- Revision guard blocks edit if `RevisionModeService.guardEdit` returns true; modal does not open.
- WebSocket disconnect: live updates stop; dirty fields remain tracked but server data is stale.
- Save conflict (`result.type === 'conflict'`): session still closes; user must re-edit.
- Contractor change delete-then-create fails mid-flight: token may be deleted but not recreated; backend state inconsistent.
- `fetchBuildingLevelsIfNeeded` returns placeholder immediately and updates asynchronously; form may show stale level list briefly.
- `entity_deleted` or `schedule_group_deleted` WS event handled independently by constructor subscription; session may close abruptly.
