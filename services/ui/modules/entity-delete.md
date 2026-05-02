---
service: ui
summary: Delete orchestration, schedule-aware confirmation, bulk ops, and modal result handlers.
paths:
  - src/app/services/entity-delete-orchestrator.service.ts
  - src/app/services/entity-bulk-ops.service.ts
  - src/app/services/modal-result-bulk-ops.service.ts
flows:
  - Delete confirmation
  - Schedule-aware deletion
  - Batch delete
  - Active feature delete
  - Building delete
  - Selection-based delete
  - Bulk lock/unlock
  - Clear-all per type
  - Modal result reload
touches:
  - HTTP (entity delete, geometadata delete, bulk lock, property updates)
  - Browser confirm dialog
external:
  - services/entity-operations.service.ts::EntityOperationsService
  - services/schedule-orchestration.service.ts::ScheduleOrchestrationService
  - services/undo.service.ts::UndoService
  - handlers/undo-executor.handler.ts::UndoExecutorHandler
  - services/entity.service.ts::EntityService
  - services/selection.service.ts::SelectionService
  - services/geometadata.service.ts::GeometadataService
  - services/message.service.ts::MessageService
  - services/revision-mode.service.ts::RevisionModeService
  - services/building-focus.service.ts::BuildingFocusService
  - services/planning-cycle.service.ts::PlanningCycleService
  - services/data-lock.service.ts::DataLockService
  - services/entity-modal-orchestrator.service.ts::EntityModalOrchestrator
  - services/road-editor-state.service.ts::RoadEditorStateService
  - services/poi.service.ts::PoiService
  - services/data-load.service.ts::DataLoadService
  - services/modal.service.ts::ModalService
  - services/entity-visibility.service.ts::EntityVisibilityService
  - services/site-context.service.ts::SiteContextService
  - api.service.ts::ApiService
  - handlers/modal-result.service.ts::ModalResultService
  - dashboard/properties-panel/properties-panel.component.ts::PropertyFieldEdit
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Handles entity deletion with schedule-group awareness, confirmation dialogs, undo recording, and multi-select batch operations. `EntityDeleteOrchestrator` routes single and bulk deletes through the per-kind handler table while respecting revision mode, data locks, and planning cycle scope. `EntityBulkOpsService` provides broader bulk operations including clear-all and properties-panel routing.

## Interface
- `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator` — Schedule-aware confirmed delete for workers, plants, and areas; single-item, multi-select, active feature, and building deletion; undo recording and selection cleanup.
- `services/entity-delete-orchestrator.service.ts::BatchDeleteResult` — Per-entity outcome type for batch deletes.
- `services/entity-delete-orchestrator.service.ts::DeleteCallbacks` — Dashboard-side callback contract for pending-cuts cleanup, vertex-edit stop, and road/POI/delivery deletion.
- `services/entity-bulk-ops.service.ts::EntityBulkOpsService` — Bulk lock/unlock, clear-all per entity type, properties panel field edits, floor selection, and delete routing.
- `services/modal-result-bulk-ops.service.ts::ModalResultBulkOpsHandler` — Subscribes to copy, bulk import, bulk edit, and wipe modal results and reloads affected entity types.

## State
- `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator` holds `callbacks: DeleteCallbacks | null` — set once by the dashboard facade. All other runtime state lives in injected services.

## Internals
- **Delete confirmation**: `EntityDeleteOrchestrator.deleteWithSchedulingAndConfirmation` checks revision guard, then `services/schedule-orchestration.service.ts::ScheduleOrchestrationService.showScheduleScopeIfGrouped`. If grouped, returns early. Otherwise `confirmDelete` picks message based on `services/planning-cycle.service.ts::PlanningCycleService.appMode`: `editing_plan` warns about tombstoning at next actualization. `skipConfirmation` bypasses the dialog.
- **Execute delete**: `EntityDeleteOrchestrator.executeDelete` re-checks revision guard, then `services/data-lock.service.ts::DataLockService.isEntityLocked`. Locked → immediate error toast. Pre-delete hook stops vertex edit for areas. Calls `services/entity-operations.service.ts::EntityOperationsService.delete`. On success: records undo via `handlers/undo-executor.handler.ts::UndoExecutorHandler.record`, clears selection per kind, clears pending cuts for areas. On failure, error toast.
- **Batch delete**: `EntityDeleteOrchestrator.deleteMultipleSelected` resolves `services/selection.service.ts::SelectionService.selectedEntities` IDs to objects via `services/entity.service.ts::EntityService`, snapshots into Maps, then calls `deleteMany`. `deleteMany` maps each entity to `deleteOneForBatch` and runs them in parallel via manual `Observable` aggregation. `deleteOneForBatch` checks data lock and calls `EntityOperationsService.delete`. On completion: clears spatial and typed selections, records one compound `services/undo.service.ts::UndoCommand` (`UndoService.record`) containing only successfully deleted items, shows partial-success message when errors exist.
- **Active feature delete**: `EntityDeleteOrchestrator.deleteActiveFeature` checks revision guard, confirms, stops vertex edit, then tries `EntityService.areas` lookup. Area found → `deleteArea` with skipped confirmation. Else → `services/geometadata.service.ts::GeometadataService.deleteFeature`.
- **Building delete**: `EntityDeleteOrchestrator.deleteBuilding` checks revision guard, confirms irreversible delete, calls `GeometadataService.deleteFeature`. On success, deselects via `services/building-focus.service.ts::BuildingFocusService.deselectBuilding` if it was the selected building.
- **Selection-based delete**: `EntityDeleteOrchestrator.deleteSelectedItem` checks multi-select first → `deleteMultipleSelected`. Else reads all single-selection slots (`selectedToken`, `selectedPlant`, `selectedRoad`, `selectedPoi`, `selectedActiveFeature`, `selectedBuilding`) and dispatches to the appropriate handler.
- **Bulk lock/unlock**: `EntityBulkOpsService.bulkLockAll` filters `selectedEntities` into a `SpatialEntityCollection`, maps to `EntityOperationsService.setLocked`, runs via `forkJoin` with `catchError(() => of(null))` to swallow per-item failures. Reports succeeded/failed counts.
- **Clear-all**: `EntityBulkOpsService.clearWorkers`, `clearPlant`, `clearAllSiteData`, `clearAllRoads`, `clearAllPois` use `Promise.all` or `forkJoin` of direct API calls. On failure, reloads affected store via `services/data-load.service.ts::DataLoadService` to re-sync UI.
- **Properties panel routing**: `EntityBulkOpsService.onPropertiesFieldEdit` updates name for worker/plant/area. Worker update requires `selectedToken.position_wgs84` for the mandatory lon/lat payload. `onPropertiesEditRequested` resolves entity and opens the relevant modal via `services/entity-modal-orchestrator.service.ts::EntityModalOrchestrator`. `onPropertiesDeleteRequested` resolves entity and delegates to `EntityModalOrchestrator` or internal delete methods.
- **Modal result handler**: `ModalResultBulkOpsHandler.start` subscribes to four `handlers/modal-result.service.ts::ModalResultService` result tokens: `COPY_TOKENS_COPIED`, `BULK_IMPORT_IMPORTED`, `BULK_EDIT_APPLIED`, `WIPE_COMPLETE`. `onTokensCopied` reloads tokens and plants. `onBulkImportCompleted` reloads tokens, plants, and areas. `onBulkEditApplied` reloads all spatial types and clears typed and spatial selections. `onWipeComplete` reloads tokens and clears token selection.

## Touches
- HTTP via `EntityOperationsService.delete`, `EntityOperationsService.setLocked`, `GeometadataService.deleteFeature`, `ApiService.deleteToken`, `ApiService.deletePlant`, `ApiService.deleteArea`, `ApiService.deleteRoad`, `PoiService.deletePoI`, `EntityService.updateToken`, `EntityService.updatePlant`, `EntityService.updateArea`.
- Browser `confirm` dialog.

## Gotchas
- `confirm` is synchronous and blocking.
- `deleteMany` runs deletes in parallel; result order is non-deterministic.
- `deleteMultipleSelected` snapshots before deletion but does not pre-check data locks for the whole batch; locks are evaluated per-entity inside `deleteOneForBatch`.
- Compound undo for batch delete only includes successfully deleted items.
- `onPropertiesFieldEdit` for workers reads `selectedToken.position_wgs84` at call time; stale selection sends wrong coordinates.
- `clearWorkers` and `clearPlant` use `toPromise()` on raw API observables; overlapping clear calls can race.
- `ModalResultBulkOpsHandler` subscribes once per app lifetime in `start()`; omitting the call leaves result tokens unhandled.
- `deleteActiveFeature` confirms once at the top; if the entity resolves as an area, the second confirmation is skipped. If it falls through to geometadata delete, the noun in the pre-confirmed message may mismatch the actual entity kind.
