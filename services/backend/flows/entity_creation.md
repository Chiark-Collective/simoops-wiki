---
trigger: { channel: http, ref: "POST /api/tokens/ | /api/plants/ | /api/zones/ | /api/areas/" }
services: [backend]
contracts: []
external: []
---

## Trigger
HTTP POST to an entity creation endpoint with entity payload and Bearer token.

## Steps
1. API route extracts and validates the Bearer token via `core_auth::authenticate_token`
2. Route calls `core_rbac::require_site_permission` with `Permission.entity_create`
3. `entity_service.py::EntityServiceBase.create_entity` verifies `data_lock` via `require_not_locked`
4. Subclass `_build_entity` constructs the model instance from payload
5. `session.add(entity)` stages the insert
6. `audit_service.py::AuditService.record` writes an audit row with snapshot
7. `session.commit()` persists entity + audit atomically
8. `entity_broadcast.py::broadcast_entity_event` serialises the response and calls `invalidate_and_broadcast`
9. `invalidate_clash_cache` schedules debounced clash recomputation via `clash_cache.schedule_recomputation`
10. `websocket_runtime::ws_manager.broadcast_entity_event` publishes to Redis pub/sub
11. WebSocket subscribers in `site:{site_id}` receive `entity_created` event

## Side effects
- PostGIS INSERT into entity table
- Audit log INSERT with full snapshot
- Redis pub/sub message to WebSocket subscribers
- Debounced clash recomputation scheduled (CPU-bound, async)

## Failure modes
| Failure | Detection | Handling |
|---|---|---|
| Invalid geometry | `shapely` validation in `_build_entity` or serializer | 400 with validation error |
| Unauthorized site | `core_rbac::require_site_permission` | 403 Forbidden |
| Data lock | `require_not_locked` raises 403 | 403 with lock detail |
| WebSocket down | Redis disconnect | Event queued in memory buffer (see gotchas) |
| Clash engine timeout | Task timeout | Clashes stale until next mutation |
