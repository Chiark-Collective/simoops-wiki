---
service: ui
channel: websocket
---

# WebSocket API

Real-time bidirectional channel. Connects to backend `websocket_runtime.md`.

## Connection Lifecycle

| Step | What |
|---|---|
| Connect | `WebSocketConnection` opens WS to `/ws` with auth token |
| Authenticate | Server validates token, assigns socket ID |
| Subscribe rooms | Client sends `subscribe_room` for `site:{id}` and `user:{id}` |
| Catch-up | Server sends `catch_up_response` with missed events since last `seq` |
| Heartbeat | Periodic ping/pong keeps connection alive |
| Reconnect | Exponential backoff on disconnect; replay `subscribe_room` and catch-up |

## Client → Server Messages

| Message | Payload | When |
|---|---|---|
| `subscribe_room` | `{ room: string }` | On site select, on reconnect |
| `unsubscribe_room` | `{ room: string }` | On site change, logout |
| `presence_heartbeat` | `{ viewport: Bounds, timestamp: number }` | Every 5s while dashboard active |
| `entity_broadcast` | `{ action, entity_type, entity_id, payload }` | Entity create/update/delete |
| `ephemeral_position` | `{ entity_type, entity_id, lon, lat }` | Token drag on map |
| `ephemeral_plant_radius` | `{ plant_id, radius_m }` | Plant radius change |
| `ephemeral_token_radius` | `{ token_id, radius_m }` | Worker radius change |
| `ephemeral_plant_arc` | `{ plant_id, start_angle, end_angle }` | Plant arc change |
| `vertex_op` | `{ layer_id, area_id, ops: [...] }` | Polygon vertex edit (OT) |
| `request_catch_up` | `{ room, last_seq }` | After reconnect |

## Server → Client Events

| Event | Payload | Consumer |
|---|---|---|
| `entity_event` | `{ action, entity_type, entity_id, payload, seq }` | `WebSocketEventRouterService` → domain services |
| `clash_results` | `{ clashes: [...] }` | `ClashStateService` |
| `presence_event` | `{ type, user_id, data }` | `PresenceService` |
| `catch_up_response` | `{ room, events, next_seq }` | `WebSocketService` replays into `events$` |
| `vertex_op_ack` | `{ area_id, applied_seq, rejected_ops }` | `VertexEditService` |
| `ephemeral_position` | `{ entity_type, entity_id, lon, lat }` | Map renders remote cursor |

## Room Semantics

| Room | Who subscribes | Lifecycle |
|---|---|---|
| `site:{site_id}` | Every dashboard session | Subscribe on site select, unsubscribe on change |
| `user:{user_id}` | Every authenticated session | Subscribe on auth, unsubscribe on logout |

## Sequence Tracking

Per-room monotonic sequence numbers. `WebSocketService` tracks `lastReceivedSeq` per room. On reconnect, sends `request_catch_up` with last known `seq`. Server returns missed events. Gap → full reload.
