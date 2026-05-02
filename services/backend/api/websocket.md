---
service: backend
channel: websocket
---

# WebSocket API

## Connection

- Path: `/ws/entities`
- Auth: JWT in `?token=` query param; validated by `core_auth::authenticate_token`
- Protocol: JSON messages; close code `1008` on auth failure
- Ping/pong: client sends `ping`; server replies `pong` and updates `last_pong`

## Client → Server

| Message | Payload | Handler | Notes |
|---|---|---|---|
| `subscribe` | `{ site_id }` | `_handle_subscribe` | Joins `site:{site_id}` room |
| `catch_up` | `{ site_id, last_seq? }` | `_handle_catch_up` | Replays missed sequenced events |
| `ping` | — | `_handle_ping` | Heartbeat |
| `presence_update` | `{ editing_entity_id?, editing_entity_type? }` | `_handle_presence_update` | Editing focus broadcast |
| `presence_heartbeat` | — | `_handle_presence_heartbeat` | Refreshes presence TTL |
| `presence_viewport` | `{ lon, lat, zoom? }` | `_handle_presence_viewport` | Map center broadcast |
| `get_presence` | `{ site_id }` | `_handle_get_presence` | Returns room snapshot |
| `ephemeral_position` | `{ entity_type, entity_id, lon, lat }` | `_handle_ephemeral_position` | Drag position; rate-limited |
| `ephemeral_token_radius` | `{ entity_id, radius_m }` | `_handle_ephemeral_token_radius` | Drag radius; rate-limited |
| `ephemeral_plant_radius` | `{ entity_id, working_radius_m, inactive_radius_m }` | `_handle_ephemeral_plant_radius` | Drag radius pair; rate-limited |
| `ephemeral_plant_arc` | `{ entity_id, arc_start_deg, arc_end_deg }` | `_handle_ephemeral_plant_arc` | Drag arc; rate-limited |
| `vertex_op` | `{ feature_id, op_type, base_rev?, ... }` | `_handle_vertex_op` | OT polygon edit |

## Server → Client

| Event | Category | Trigger | Notes |
|---|---|---|---|
| `entity_created` | Entity | CRUD | Sequenced, logged |
| `entity_updated` | Entity | CRUD | Sequenced, logged; delta included |
| `entity_deleted` | Entity | CRUD | Sequenced, logged |
| `schedule_group_deleted` | Entity | CRUD | Sequenced, logged |
| `context_invalidated` | Context | Permission change | Forces client re-subscribe |
| `user_joined` | Presence | Subscribe | Auto-broadcast |
| `user_left` | Presence | Disconnect | Auto-broadcast |
| `presence_snapshot` | Presence | Subscribe / Request | Sent on room join |
| `presence_changed` | Presence | Presence update | Editing focus change |
| `presence_viewport` | Presence | Viewport change | Map center update |
| `ephemeral_position` | Ephemeral | Client drag | Rate-limited, no seq |
| `ephemeral_token_radius` | Ephemeral | Client drag | Rate-limited, no seq |
| `ephemeral_plant_radius` | Ephemeral | Client drag | Rate-limited, no seq |
| `ephemeral_plant_arc` | Ephemeral | Client drag | Rate-limited, no seq |
| `vertex_op_applied` | VertexOp | Vertex op | Broadcast to others |
| `vertex_op_ack` | VertexOp | Vertex op | ACK/NACK to sender |
| `clash_results_updated` | Clash | Detection run | — |
| `planning_cycle_updated` | Planning | Cycle edit | — |
| `planning_carry_forward` | Planning | Carry-forward | — |
| `planning_baseline_imported` | Planning | Baseline import | — |
| `planning_actualized` | Planning | Actualize | — |
| `planning_submission_updated` | Planning | Submission | — |
| `planning_submissions_bulk_updated` | Planning | Bulk submission | — |
| `data_lock_changed` | DataLock | Lock toggle | — |
| `geometry_cut` | Geometry | Geometry op | — |
| `geometry_restored` | Geometry | Geometry op | — |
| `bulk_import_completed` | BulkImport | Import finish | — |
| `permit_count_updated` | Permit | Permit change | — |
| `config_changed` | Config | Config update | — |
| `catch_up_response` | CatchUp | catch_up request | Replay or `full_reload_required` |
| `subscribed` | Control | subscribe | Includes `current_seq` |
| `pong` | Control | ping | Heartbeat reply |
| `error` | Control | Invalid action | Error detail string |

## Rooms

| Pattern | Members | Lifecycle |
|---|---|---|
| `site:{site_id}` | All connected clients for site | Created on first subscribe |

## Key Behaviours

- Catch-up replay: replays missed sequenced events from `event_log`; gap too large → `full_reload_required`
- Re-subscribe re-fetches User row so live permission changes take effect immediately
- Ephemeral events: local-only, no sequence number, no persistence, ~15/sec rate limit
- Sender exclusion: ephemeral events broadcast to room but never echoed back to sender
- Permission filtering: every event passes through `_filter_event_for_user` before delivery
