---
trigger: { channel: http, ref: "POST /api/tokens/" }
services: [backend]
contracts: []
external: []
---

# Entity Creation

## Trigger

HTTP POST to `/api/tokens/` (or `/api/zones/`, `/api/plants/`, etc.) with entity payload.

## Steps

1. API route validates Bearer token via `auth.py::get_current_user`
2. Route extracts `site_id` from payload or path
3. `EntityService.create_entity(session, site_id, data)` persists to PostGIS
4. Geometry validated via `shapely` and reprojected if needed
5. `EntityBroadcast.emit_entity_created(site_id, entity)` publishes WebSocket event
6. WebSocket manager broadcasts `entity_created` to all clients in `site:{site_id}` room
7. `ClashDetectionService` triggered asynchronously if entity has spatial bounds
8. Clash engine recomputes for site + current shift
9. New clashes emitted via WebSocket `clash_updated`

## Side effects

- PostGIS INSERT into entity table
- Redis pub/sub message to WebSocket subscribers
- Possible clash recomputation (CPU-bound)
- Audit log entry via `audit_service`

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| Invalid geometry | `shapely` exception | 400 with validation error |
| Unauthorized site | RBAC check | 403 |
| WebSocket down | Redis disconnect | Event queued in memory buffer (see gotchas) |
| Clash engine timeout | Task timeout | Clashes stale until next mutation |
