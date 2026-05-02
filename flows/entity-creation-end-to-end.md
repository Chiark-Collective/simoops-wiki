---
trigger: { channel: ui, ref: "FAB add action" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User clicks the Add FAB, selects an entity type, and places it on the map.

## Steps
1. `fab-menu.component.ts` emits `@Output() createWorker`, `startAreaCreation`, or `openPlantModal`.
2. `dashboard.component.ts` binds outputs and delegates to `EntityCreationHostComponent`.
3. `EntityCreationHostComponent` routes to `WorkerCreationWorkflowService`, `PlantCreationWorkflowService`, or `AreaReferenceCreationWorkflowService`.
4. `MapComponent` reads creation mode from `EntityCreationOrchestrator` state; `updateModeCursor()` sets custom cursor.
5. `map-event-wiring.ts` click handler emits position event; `MapEventDispatchService` routes to callback.
6. Workflow opens modal with building check; on submit, handler (`worker.handler.ts`, `plant.handler.ts`, or `area.handler.ts`) invokes `EntityService.createToken()` / `createPlant()` / `createArea()`.
7. `EntityService` calls `ApiService.createToken()` / `createPlant()` / `createArea()` → HTTP POST with Bearer token, `planning_cycle_id` from `PlanningCycleService`, and temporal context from `TemporalContextService`.
8. Optimistic update: `EntityService` calls `store.add(token/plant/area)` immediately on HTTP response.
9. Backend route (`workers.py::create_worker`, `plant.py::create_plant`, or `geometadata.py::create_zone_feature`) validates JWT via `core_auth::authenticate_token` and RBAC via `core_rbac::require_site_permission` with `Permission.entity_create`.
10. `entity_service.py::EntityServiceBase.create_entity` enforces `data_lock` via `require_not_locked`; subclass `_build_entity` constructs model from payload.
11. `session.add(entity)` stages insert; `audit_service.py::AuditService.record` writes audit snapshot; `session.commit()` persists entity + audit atomically.
12. If entity carries schedule data, `schedule_reconcile.py` may generate occurrences.
13. `entity_broadcast.py::broadcast_entity_event` serialises response and calls `invalidate_and_broadcast`.
14. `invalidate_clash_cache` schedules debounced clash recomputation via `clash_cache.schedule_recomputation`.
15. `websocket_runtime.py::ws_manager.broadcast_entity_event` publishes `entity_created` to Redis pub/sub; subscribers in room `site:{site_id}` receive event.
16. Frontend `WebSocketEventRouterService.routeEntityEventBatch()` routes `entity_created` to `EntityService.wsAddToken()` / `wsAddPlant()` / `wsAddArea()`.
17. `EntityService.wsAdd*` calls `EntityStore.add()`; store reconciles duplicates by ID so optimistic add and WS add for the same ID coalesce.
18. `FilteredEntityCacheService` emits on store update; `MapSubscriptionOrchestrator` sets dirty flags and schedules map update.
19. `MapComponent` `MapDirtyFlagScheduler` flushes per RAF; `updateBeacons()`, `updatePlantSource()`, `updateGeometadataSource()` refresh map sources.

## Side effects
- HTTP POST `POST /api/workers/`, `POST /api/plant`, or `POST /api/geometadata/zones`.
- PostGIS INSERT into entity table; audit log INSERT with full snapshot.
- Optimistic update: `EntityStore` per-type BehaviorSubject emits new collection immediately on HTTP response.
- `entity_created` WebSocket broadcast to all clients in room `site:{site_id}`.
- Redis pub/sub message published and consumed.
- Debounced clash recomputation scheduled (CPU-bound, async).
- MapLibre GeoJSON sources recreated for tokens, plants, areas.

## Failure modes
- **Invalid geometry**: `shapely` validation in `_build_entity` or serializer → 400 with validation error.
- **Unauthorized site**: `core_rbac::require_site_permission` → 403 Forbidden.
- **Data lock**: `require_not_locked` raises 403 with lock detail.
- **WebSocket down**: Redis disconnect → event queued in memory buffer.
- **Optimistic/WS duplicate**: `EntityStore.add()` reconciles by ID; optimistic add and WS add for same ID coalesce without duplicate render.
- **Clash engine timeout**: task timeout → clashes stale until next mutation.
- **Clash cache invalidation expensive**: large sites trigger heavy recomputation on every entity creation.
- **Building check miss**: no building at click position → creation proceeds without building context.
- **Area vertex mistiming**: double-click vs rapid placement; pixel distance ≤5px finish check may add unwanted vertices.
- **Map state loss**: source recreation resets filters and layout properties; visibility/selection state must be reapplied.

## Cross-references
- [frontend journey](../services/ui/flows/entity-creation-on-map.md)
- [backend sequence](../services/backend/flows/entity_creation.md)
- [HTTP contract](../contracts/ui-backend/http-contract.md)
- [WebSocket contract](../contracts/ui-backend/websocket-contract.md)

## Gotchas
- Frontend optimistic update precedes authoritative WS broadcast; `EntityStore.add()` deduplicates by ID so the WS add is a no-op if the optimistic add already exists.
- Backend broadcast uses `_broadcast_event` helper; `text_label_service.py` bypasses it with direct `ws_manager.broadcast_entity_event`.
- Clash cache invalidation on backend may be expensive for large sites.
