---
service: backend
channel: websocket
---

# WebSocket API

## Connection

- Path: `/ws`
- Auth: Bearer token in query param `?token=`
- Protocol: JSON messages

## Client → Server

| Message | Payload | Handler | Notes |
|---|---|---|---|
| `subscribe` | `{ room: "site:{site_id}" }` | `websocket_manager` | Join site room |
| `unsubscribe` | `{ room: "site:{site_id}" }` | `websocket_manager` | Leave site room |
| `presence_update` | `{ lat, lng, viewport }` | `presence_manager` | Share location |
| `vertex_op` | `{ entity_id, ops[] }` | `vertex_op_store` | Collaborative geometry edit |

## Server → Client

| Event | Payload | Trigger | Notes |
|---|---|---|---|
| `entity_created` | `{ entity_type, entity_id, site_id }` | Entity CRUD | Broadcast to site room |
| `entity_updated` | `{ entity_type, entity_id, site_id, changes }` | Entity CRUD | Delta included |
| `entity_deleted` | `{ entity_type, entity_id, site_id }` | Entity CRUD | Tombstone |
| `clash_updated` | `{ clash_id, severity, entity_ids }` | Clash engine | New or resolved clash |
| `presence_broadcast` | `{ user_id, lat, lng, viewport }` | Presence manager | Throttled |
| `vertex_ack` | `{ op_id, status }` | Vertex OT | Operation accepted/rejected |
| `lock_acquired` | `{ resource, user_id }` | `data_lock` | Admin lock change |

## Rooms

| Room Pattern | Members | Lifecycle |
|---|---|---|
| `site:{site_id}` | All connected clients for site | Created on first subscribe, empty → destroyed |
| `presence:{site_id}` | Clients sharing location | Subset of site room |

## Failure Modes

- Token invalid → connection rejected with 403
- Room not found → silent ignore
- Redis down → fallback to in-memory event buffer (see gotchas.md)
