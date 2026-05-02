---
trigger: { channel: ui, ref: "entity edit save" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User clicks Save in the entity edit modal after modifying fields.

## Steps
1. `EntityEditModalComponent.onConfirm` emits `(confirm)` → `EntityModalOrchestrator.onEditModalConfirm`.
2. `EntityModalOrchestrator` → `EntityEditOrchestrator.confirmEditModal` → `saveSingleEntity`.
3. `saveSingleEntity` calls `EntityEditSessionService.save`.
4. `EntityEditSessionService.save` invokes `EditSaveHandler.save`.
5. Handler branches by entity type:
   - Worker: `handlers/worker.handler.ts::WorkerHandler.editWorker` → `EntityService.updateToken` → HTTP PATCH/PUT `/api/tokens/{id}`.
   - Plant: `handlers/plant.handler.ts::PlantHandler.editPlant` → `EntityService.updatePlant` → HTTP PATCH/PUT `/api/plants/{id}`.
   - Area: `handlers/area.handler.ts::AreaHandler.editArea` → `EntityService.updateArea` → HTTP PATCH/PUT `/api/areas/{id}`.
6. Contractor mutation on worker: `EditSaveHandler.saveToken` detects `contractor_id` change → `recreateTokenWithNewContractor` → `EntityService.deleteToken` → `EntityService.createToken` → `EntityService.updateToken`; backend disallows direct `contractor_id` mutation.
7. Backend route receives request; `core_auth::authenticate_token` validates Bearer token.
8. Route calls `core_rbac::require_site_permission` with `Permission.entity_edit`.
9. `services/token_service.py::update_token` (or plant/area equivalent) loads entity and verifies contractor access.
10. `data_lock` check via `require_not_locked` on the entity's current `end_at`.
11. `_check_optimistic_concurrency` compares `expected_updated_at` and field groups; raises 409 on conflict.
12. Pre-update snapshot captured via `audit_service.py::snapshot_entity`.
13. `_apply_updates` mutates entity fields in place.
14. `_record_modified_fields` updates `last_modified_fields` for future OCC.
15. `_stamp_audit_fields` sets `updated_by` and contractor metadata in `extra`.
16. `reevaluate_cycle_membership` drops planning cycle tags if the occurrence moved outside the window.
17. `session.commit()` persists entity + audit row atomically.
18. `entity_broadcast.py::broadcast_update_delta` computes semantic delta and calls `broadcast_entity_event`.
19. `invalidate_clash_cache` schedules debounced clash recomputation; position/geometry changes trigger cache invalidation.
20. `websocket_runtime::ws_manager.broadcast_entity_event` publishes `entity_updated` with delta to Redis.
21. Editing client: `EntityEditSessionService.subscribeToLiveUpdates` receives WS `entity_updated` for matching `entity_id`; merges fresh server data into `session.entity` while preserving `dirtyFields`.
22. Other clients: `entity_updated` → `EntityService.wsUpdateToken` → store update → map refresh.
23. If schedule fields changed, `schedule_reconcile.py` may add or remove occurrences asynchronously.
24. Clash recomputation completes; updated clashes broadcast via `clashResults$`.
25. On success (`result.type === 'saved'` or `'conflict'`), `EntityEditSessionService.save` calls `closeSession`.
26. `closeSession` unsubscribes live WS updates, emits `_session.next(null)`, calls `presenceService.stopEditing`, and `modalService.closeIf('entity-edit')`.
27. `EntityEditOrchestrator.saveSingleEntity` does NOT call `loadTokens()` after save because `loadTokens` uses `selectedShift`, which would erase cross-shift tokens.

## Side effects
- HTTP PATCH/PUT to backend entity endpoints; worker contractor change triggers delete-then-create sequence.
- PostGIS UPDATE of entity row; atomic audit log INSERT with field-level diff (`changes`) and post-update snapshot.
- Redis pub/sub `entity_updated` message carrying delta fields for client-side merge.
- WebSocket presence: `startEditing` / `stopEditing`.
- `EditSession` state mutation: `dirtyFields`, merged entity data.
- Modal open/close state.
- Debounced clash cache invalidation and recomputation.
- Schedule reconciliation if schedule fields changed.

## Failure modes
- OCC conflict: `expected_updated_at` mismatch + overlapping field groups → 409 with `current` entity and `conflicting_fields`; session still closes; user must re-edit.
- Data lock: `require_not_locked` raises 403 → 403 with lock detail.
- Unauthorized: RBAC or contractor access check fails → 403 Forbidden.
- Entity not found → 404.
- Geometry invalid → 400.
- WebSocket disconnect: live updates stop; dirty fields remain tracked but server data is stale.
- Contractor change delete-then-create fails mid-flight: token may be deleted but not recreated; backend state inconsistent.
- `entity_deleted` or `schedule_group_deleted` WS event handled independently by constructor subscription; session may close abruptly.
- Pre-migration audit entries cannot be reverted (snapshot is None).
- Audit-revert geometry SRID fallback defaults to 3857.

## Cross-references
- [frontend journey](../services/ui/flows/entity-edit-session.md)
- [backend sequence](../services/backend/flows/entity_update.md)
- [HTTP contract](../contracts/ui-backend/http-contract.md)
- [WebSocket contract](../contracts/ui-backend/websocket-contract.md)
