---
trigger: { channel: http, ref: "PATCH /api/tokens/{id} | /api/plants/{id} | /api/areas/{id}" }
services: [backend]
contracts: []
external: []
---

## Trigger
HTTP PATCH or PUT to an entity update endpoint with partial payload and Bearer token.

## Steps
1. API route validates Bearer token via `core_auth::authenticate_token`
2. Route calls `core_rbac::require_site_permission` with `Permission.entity_edit`
3. `entity_service.py::EntityServiceBase.update_entity` loads entity and verifies contractor access
4. `data_lock` check via `require_not_locked` on the entity's current `end_at`
5. `_check_optimistic_concurrency` compares `expected_updated_at` and field groups; raises 409 on conflict
6. Pre-update snapshot captured via `audit_service.py::snapshot_entity`
7. `_apply_updates` mutates entity fields in place
8. `_record_modified_fields` updates `last_modified_fields` for future OCC
9. `_stamp_audit_fields` sets `updated_by` and contractor metadata in `extra`
10. `reevaluate_cycle_membership` drops planning cycle tags if the occurrence moved outside the window
11. `session.commit()` persists entity + audit row atomically
12. `entity_broadcast.py::broadcast_update_delta` computes semantic delta and calls `broadcast_entity_event`
13. `invalidate_clash_cache` schedules debounced clash recomputation
14. `websocket_runtime::ws_manager.broadcast_entity_event` publishes `entity_updated` with delta to Redis
15. WebSocket subscribers receive `entity_updated` event with changed field list

## Side effects
- PostGIS UPDATE of entity row
- Audit log INSERT with field-level diff (`changes`) and post-update snapshot
- Redis pub/sub message carrying delta fields for client-side merge
- Debounced clash recomputation scheduled

## Failure modes
| Failure | Detection | Handling |
|---|---|---|
| OCC conflict | `expected_updated_at` mismatch + overlapping field groups | 409 with `current` entity and `conflicting_fields` |
| Data lock | `require_not_locked` raises 403 | 403 with lock detail |
| Unauthorized | RBAC or contractor access check fails | 403 Forbidden |
| Entity not found | `get_or_404` on missing ID | 404 |
| Geometry invalid | Validation in `_apply_updates` | 400 |
