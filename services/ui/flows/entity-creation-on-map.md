---
trigger: { channel: ui, ref: "FAB add action" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User clicks the Add FAB and selects an entity type to create.

## Steps
1. `dashboard/fab-menu/fab-menu.component.ts::FabMenuComponent` emits `@Output() createWorker`, `startAreaCreation`, or `openPlantModal`.
2. `dashboard/dashboard.component.ts::DashboardComponent` template binds `(createWorker)="createWorker()"`, `(startAreaCreation)="startAreaCreation()"`, `(openPlantModal)="openPlantModal()"`; delegates to `creationHost`.
3. `dashboard/entity-creation-host/entity-creation-host.component.ts::EntityCreationHostComponent` `createWorker()` → `workerWorkflow.createWorker()`; `startAreaCreation()` → `areaReferenceWorkflow.startAreaCreation()`; `openPlantModal()` → `plantWorkflow.openPlantModal()`.
4. `services/entity-creation-orchestrator.service.ts::EntityCreationOrchestrator` `startWorkerCreation()` / `startPlantCreation()` / `startAreaCreation()` set `CreationMode` on `_state` BehaviorSubject.
5. `map/map.component.ts::MapComponent` reads `tokenCreationMode` / `plantCreationMode` / `areaCreationMode` from orchestrator state; `updateModeCursor()` sets custom cursors.
6. `map/map-event-wiring.ts` map `click` handler checks creation modes; emits `MapInteractionService` events: `token:positionSelected`, `plant:positionSelected`, `area:mapClick`.
7. `services/map-event-dispatch.service.ts::MapEventDispatchService` routes to callbacks: `onWorkerPositionSelected`, `onPlantPositionSelected`, `onAreaPointAdded`.
8. `dashboard/dashboard.component.ts::DashboardComponent` callbacks delegate back to `creationHost`.
9. Worker: `dashboard/entity-creation-host/worker-creation-workflow.service.ts::WorkerCreationWorkflowService.placeWorkerWithBuildingCheck()` → `openWorkerCreationModalWithPosition()` → `ModalService.open(WORKER_CREATION_MODAL, ...)`.
10. Plant: `dashboard/entity-creation-host/plant-creation-workflow.service.ts::PlantCreationWorkflowService.placePlantWithBuildingCheck()` → `openPlantCreationModalWithPosition()` → `ModalService.openPlantCreation(...)`.
11. Area: `dashboard/entity-creation-host/area-reference-creation-workflow.service.ts::AreaReferenceCreationWorkflowService` collects polygon points via `onAreaPointAdded()`; on finish (`onAreaFinished()`) opens area creation modal.
12. Worker form submit: `dashboard/entity-creation-host/worker-creation-workflow.service.ts::onWorkerCreationPlace()` → `handlers/worker.handler.ts::WorkerHandler.createWorker()`.
13. Plant form submit: `dashboard/entity-creation-host/plant-creation-workflow.service.ts::onPlantCreationPlace()` → `handlers/plant.handler.ts::PlantHandler.createPlant()`.
14. Area form submit: `dashboard/entity-creation-host/area-reference-creation-workflow.service.ts::onAreaCreationSave()` → `handlers/area.handler.ts::AreaHandler.createArea()`.
15. `services/planning-cycle.service.ts::PlanningCycleService.getCycleIdForCreation$()` — `editing_plan` returns cycle id (planned entities); `editing_actual` returns `undefined` (baseline/actual rows).
16. `services/temporal-context.service.ts::TemporalContextService.creationContext$` provides `shiftId`, `workDate`, `defaultTimeRange`, `startAt`/`endAt` ISO datetimes for temporal alignment.
17. `services/entity.service.ts::EntityService` `createToken()` → `ApiService.createToken()`; `createPlant()` → `ApiService.createPlant()`; `createArea()` → `ApiService.createArea()`.
18. Optimistic update: `EntityService.createToken()` → `tap(token => tokenStore.add(token))`; `createPlant()` → `tap(plant => plantStore.add(plant))`; `createArea()` → `tap(area => areaStore.add(area))`.
19. `services/entity-store.ts::EntityStore` `add(item)` pushes into BehaviorSubject.
20. WebSocket `entity_created` broadcast: `services/websocket-event-router.service.ts::WebSocketEventRouterService.routeEntityEventBatch()` → worker: `entityService.wsAddToken(data)`; plant: `wsAddPlant(data)`; area: `wsAddArea(mapAreaData(d))`.
21. `services/entity.service.ts` `wsAddToken()` / `wsAddPlant()` / `wsAddArea()` call `store.add()` (reconciles duplicates).
22. `services/filtered-entity-cache.service.ts::FilteredEntityCacheService` — entity store emissions feed cache.
23. `map/map-subscription-orchestrator.ts::MapSubscriptionOrchestrator` `subscribeToEntityData()` → `filteredCache.addOnCacheUpdated(() => { ... })` → sets dirty flags → `host.scheduleMapUpdate()`.
24. `map/map.component.ts::MapComponent` `MapDirtyFlagScheduler` flushes per RAF; `updateBeacons()`, `updatePlantSource()`, `updateGeometadataSource()`.

## Side effects
- HTTP POST to backend via `ApiService.createToken` / `createPlant` / `createArea`.
- `EntityStore` per-type BehaviorSubject emits new collection.
- WebSocket `entity_created` broadcast to other clients.
- MapLibre GeoJSON sources recreated for tokens, plants, areas.
- `MapComponent` dirty flags trigger RAF-batched source updates.
- `PlanningCycleService` may tag created entity with `planning_cycle_id`.

## Failure modes
- Map source recreation resets filters and layout properties; visibility/selection state must be reapplied.
- `SiteContextService` getters return new Observable references each call; multiple subscriptions may see divergent values.
- `EntityStore` optimistic updates only for tokens and plants; area lacks 409 rollback.
- Building check fails (no building at click): creation proceeds without building context.
- Double-click vs rapid vertex placement: area finish checks pixel distance ≤5px; mistimed clicks add unwanted vertices.
- WebSocket duplicate: `EntityStore.add()` reconciles by ID; optimistic add and WS add for same ID coalesce.

## Cross-references
- [entity-creation module](../modules/entity-creation.md)
- [entity-store module](../modules/entity-store.md)
- [map-core module](../modules/map-core.md)
