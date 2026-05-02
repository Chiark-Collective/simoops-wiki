---
trigger: { channel: ui, ref: "delete key or delete button" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User presses Delete/Backspace, clicks a delete button in the properties panel or context menu, or triggers bulk delete on a multi-selection.

## Steps

1. Entry points emit delete intent:
   - Keyboard: `map/map.component.ts::MapComponent.onKeyDown` emits `MapInteractionEvent` with `type: 'general:deleteRequested'`
   - Properties panel: `dashboard/properties-panel/properties-panel.component.ts::PropertiesPanelComponent.requestDelete` emits `deleteRequested`
   - Context menu: `map/map-context-menu.component.ts::MapContextMenuComponent.onEntityContextMenuDelete` emits `type: 'contextMenu:entityDeleteRequested'`
   - Multi-selection: `dashboard/properties-panel/multi-selection-summary.component.ts` emits `bulkDeleteRequested`

2. Event routing:
   - `general:deleteRequested` → `services/map-event-dispatch.service.ts` → `services/entity-modal-orchestrator.service.ts::EntityModalOrchestrator.deleteSelectedItem` → `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator.deleteSelectedItem`
   - `deleteRequested` → `dashboard.component.html` → `services/entity-bulk-ops.service.ts::EntityBulkOpsService.onPropertiesDeleteRequested` resolves the entity → `services/entity-modal-orchestrator.service.ts::EntityModalOrchestrator.onEntityDeleted`
   - `contextMenu:entityDeleteRequested` → `services/map-event-dispatch.service.ts` → `services/entity-modal-orchestrator.service.ts::EntityModalOrchestrator.onEntityDeleteRequested` resolves entity by ID → `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator.onEntityDeleted`
   - `bulkDeleteRequested` → `dashboard.component.html` → `services/entity-modal-orchestrator.service.ts::EntityModalOrchestrator.deleteMultipleSelected`

3. Single delete — confirmation and scheduling guard:
   `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator.deleteWithSchedulingAndConfirmation` calls `services/revision-mode.service.ts::RevisionModeService.guardEdit`. If the entity is schedule-grouped (`occCount > 1`), `services/schedule-orchestration.service.ts::ScheduleOrchestrationService.showScheduleScopeIfGrouped` opens a scope modal and returns early. A mode-aware prompt is built: tombstoning warning when `services/planning-cycle.service.ts::PlanningCycleService.appMode === 'editing_plan'`, otherwise a plain prompt. `confirm(message)` blocks until the user confirms.

4. Single delete — execution:
   `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator.executeDelete` checks `services/data-lock.service.ts::DataLockService.isEntityLocked(entity)`. For areas, `services/entity-delete-orchestrator.service.ts::DeleteCallbacks.stopVertexEditIfActive` runs first. `services/entity-operations.service.ts::EntityOperationsService.delete(entity)` dispatches to `handlers/worker.handler.ts::WorkerHandler.deleteWorker`, `handlers/plant.handler.ts::PlantHandler.deletePlant`, or `handlers/area.handler.ts::AreaHandler.deleteArea`.

5. Single delete — success cleanup:
   `handlers/undo-executor.handler.ts::UndoExecutorHandler.record('delete', kind, id, label, beforeSnapshot, null)` is written. Selection is cleared via `services/selection.service.ts::SelectionService.selectToken(null)`, `selectPlant(null)`, or `selectActiveFeature(null)`. For areas, `services/entity-delete-orchestrator.service.ts::DeleteCallbacks.clearPendingCuts` runs.

6. Batch delete — preparation:
   `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator.deleteMultipleSelected` snapshots IDs, then resolves full objects via `services/entity.service.ts::EntityService`.

7. Batch delete — execution:
   `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator.deleteMany` builds an array of per-entity `Observable<BatchDeleteResult>` and aggregates results with manual subscription counting (not `forkJoin`). Each item is processed by `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator.deleteOneForBatch`, which checks `services/data-lock.service.ts::DataLockService.isEntityLocked(entity)`, calls `services/entity-operations.service.ts::EntityOperationsService.delete(entity)`, and catches errors with `catchError`.

8. Batch delete — compound undo:
   On completion, `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator.deleteMultipleSelected` builds `children: UndoCommand[]` from snapshots of successfully deleted entities and records `services/undo.service.ts::UndoService.record({ operation: 'delete', entityKind: 'worker', entityId: 'batch', children })`.

## Side effects

- HTTP `DELETE` to backend via handler (`handlers/worker.handler.ts::WorkerHandler.deleteWorker`, `handlers/plant.handler.ts::PlantHandler.deletePlant`, `handlers/area.handler.ts::AreaHandler.deleteArea`).
- WebSocket broadcast of deletion consumed by other clients.
- `handlers/undo-executor.handler.ts::UndoExecutorHandler.record` / `services/undo.service.ts::UndoService.record` appends an `UndoCommand` to the undo stack.
- `services/undo.service.ts::UndoCommand` carries `id`, `operation`, `entityKind`, `entityId`, `entityLabel`, `beforeSnapshot`, `afterSnapshot`, `timestamp`, and optional `children` for compound operations.
- Selection store mutations: `services/selection.service.ts::SelectionService.selectToken(null)`, `selectPlant(null)`, `selectActiveFeature(null)`.
- Area-specific: `services/entity-delete-orchestrator.service.ts::DeleteCallbacks.clearPendingCuts` mutates pending cut state.
- `confirm` is a synchronous blocking browser dialog.

## Failure modes

- Revision mode guard blocks edit: `services/revision-mode.service.ts::RevisionModeService.guardEdit` returns early; delete is abandoned.
- Schedule group modal intercepts: `services/schedule-orchestration.service.ts::ScheduleOrchestrationService.showScheduleScopeIfGrouped` opens a modal and the original delete returns without proceeding.
- Data-locked entity: `services/data-lock.service.ts::DataLockService.isEntityLocked(entity)` detects the lock and aborts that entity's delete with an error toast.
- Batch partial failure: `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator.deleteOneForBatch` catches per-entity errors; successful deletions still proceed and compound undo only contains successes.
- Non-deterministic batch result order: `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator.deleteMany` runs parallel subscriptions without `forkJoin`; UI must not depend on result ordering.
- Pre-checked confirmation mismatch: `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator.deleteActiveFeature` confirms once at the top; if the resolved entity is an area the second confirmation is skipped, but if it falls through to a geometadata delete the pre-confirmed message noun may not match the actual target.
