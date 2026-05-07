---
producer: backend
consumers: [ui]
schema: backend/src/entities/websocket/schemas.py
breaking_changes: []
---

## Purpose
Real-time bidirectional event stream between UI and backend for entity lifecycle, presence, ephemeral edits, and catch-up.

## Schema
See `backend/src/entities/websocket/schemas.py` for Pydantic message models.

## Consumers

| service | uses | flow |
|--------|------|------|
| ui | `WebSocketService` | `WebSocketService.send*(...)` → backend `_handle_*` → events → `WebSocketEventRouterService.routeEntityEvent` → domain handlers |

## Connection

| Parameter | Value |
|-----------|-------|
| Endpoint | `wss://host/ws/entities?token=<jwt>` |
| Auth | JWT as query param (browsers can't set WebSocket headers); validated via `authenticate_token()` (same as HTTP) |
| Per-user connection limit | 3 max; oldest evicted on #4 |
| Heartbeat | frontend ping every 30s, backend replies pong |
| Missed-pong threshold | 3 → reconnect |
| Reconnect | exponential backoff 1→2→4→8→16s, then 30s polling |
| Catch-up | per-room event log (5000 events, 30min TTL); `catch_up` action with `last_seq` |

## Frontend → Backend actions

| Action | Payload | Frontend sender | Backend handler |
|--------|---------|-----------------|-----------------|
| `subscribe` | `{ action: "subscribe", site_id: string }` | `WebSocketService.sendSubscription(siteId)` | `_handle_subscribe` |
| `ping` | `{ action: "ping" }` | `WebSocketService.ping()` | `_handle_ping` |
| `presence_update` | `{ action: "presence_update", editing_entity_id: string \| null, editing_entity_type: string \| null }` | `WebSocketService.sendPresenceUpdate(entityId, entityType)` | `_handle_presence_update` |
| `presence_heartbeat` | `{ action: "presence_heartbeat" }` | `WebSocketService.sendPresenceHeartbeat()` | `_handle_presence_heartbeat` |
| `catch_up` | `{ action: "catch_up", site_id: string, last_seq: number }` | `WebSocketService.sendCatchUp(siteId)` | `_handle_catch_up` |
| `get_presence` | `{ action: "get_presence", site_id: string }` | `WebSocketService.requestPresenceSnapshot(siteId)` | `_handle_get_presence` |
| `ephemeral_position` | `{ action: "ephemeral_position", entity_type: "worker" \| "plant", entity_id: string, lon: number, lat: number, contractor_id?: string }` | `WebSocketService.sendEphemeralPosition(...)` | `_handle_ephemeral_position` |
| `ephemeral_token_radius` | `{ action: "ephemeral_token_radius", entity_id: string, radius_m: number, contractor_id?: string }` | `WebSocketService.sendEphemeralTokenRadius(...)` | `_handle_ephemeral_token_radius` |
| `ephemeral_plant_radius` | `{ action: "ephemeral_plant_radius", entity_id: string, working_radius_m: number, inactive_radius_m: number, contractor_id?: string }` | `WebSocketService.sendEphemeralPlantRadius(...)` | `_handle_ephemeral_plant_radius` |
| `ephemeral_plant_arc` | `{ action: "ephemeral_plant_arc", entity_id: string, arc_start_deg: number, arc_end_deg: number, contractor_id?: string }` | `WebSocketService.sendEphemeralPlantArc(...)` | `_handle_ephemeral_plant_arc` |
| `presence_viewport` | `{ action: "presence_viewport", lon: number, lat: number, zoom?: number }` | `WebSocketService.sendPresenceViewport(lon, lat, zoom)` | `_handle_presence_viewport` |
| `vertex_op` | `{ action: "vertex_op", feature_id: string, base_rev: number, op_type: "move" \| "insert" \| "delete", ... }` | `WebSocketService.sendVertexOp(featureId, op, baseRev)` | `_handle_vertex_op` |

## Backend → Frontend events

### Control frames

| Event | Payload | Frontend handler |
|-------|---------|------------------|
| `subscribed` | `{ status: "subscribed", room: "site:{id}", current_seq: number }` | `_handle_subscribe` |
| `error` | `{ error: string }` | various handlers |
| `pong` | `{ action: "pong" }` | `_handle_ping` |

### Entity lifecycle (sequenced)

| Event | Payload | Frontend handler |
|-------|---------|------------------|
| `entity_created` | `{ event, entity_type, entity_id, data, seq }` | `WebSocketEventRouterService.routeEntityEvent` → domain `wsAdd*` |
| `entity_updated` | `{ event, entity_type, entity_id, data, delta?, seq }` | `routeEntityEvent` → domain `wsUpdate*` |
| `entity_deleted` | `{ event, entity_type, entity_id, data?, seq }` | `routeEntityEvent` → domain `wsRemove*` |
| `schedule_group_deleted` | `{ event, entity_type, entity_id, data?, seq }` | `routeEntityEvent` → `wsRemoveTokensByScheduleGroup` / `wsRemovePlantsByScheduleGroup` |

Entity types: `worker`, `plant`, `zone`, `feature`, `delivery`, `poi`, `text_label`, `alert`

### Clash

| Event | Payload | Frontend handler |
|-------|---------|------------------|
| `clash_results_updated` | `{ event, site_id, clashes, legacy_clashes, clash_rule_results, entity_severity, seq? }` | `ClashStateService` — dual-shape payload during ADR D1 deprecation window; `entity_severity` derived from unresolved clashes only |

### Planning lifecycle

| Event | Payload |
|-------|---------|
| `planning_cycle_updated` | `{ event, cycle_id, status, seq? }` |
| `planning_actualized` | `{ event, cycle_id, tokens_forked, plants_forked, features_forked, deliveries_forked, seq? }` |
| `planning_carry_forward` | `{ event, source_cycle_id, target_cycle_id, tokens_copied, plants_copied, features_copied, deliveries_copied, seq? }` |
| `planning_baseline_imported` | `{ event, cycle_id, tokens_imported, plants_imported, features_imported, deliveries_imported, seq? }` |
| `planning_submission_updated` | `{ event, cycle_id, contractor_id, status, submission, seq? }` |
| `planning_submissions_bulk_updated` | `{ event, cycle_id, updated_count, submissions, seq? }` |

### Config changes

| Event | Payload |
|-------|---------|
| `config_changed` | `{ event, domain, op, record_id, data, audience?, seq? }` |

Domains: `contractor`, `shift`, `label_style`, `smart_group`, `site_map`, `clash_rule`, `rule_profile`, `clash_resolution`, `report_session`, `scene_decision`, `membership`, `invite`, `invite_link`
- `contractor:updated` now triggers contractor logo sync on the frontend (re-register MapLibre images, mark beacons/delivery pins dirty)

### Context invalidation

| Event | Payload | Frontend handler |
|-------|---------|------------------|
| `context_invalidated` | `{ event, site_id, user_id?, seq? }` | forces re-subscription |

### Geometry

| Event | Payload |
|-------|---------|
| `geometry_cut` | `{ event, target_id, cutter_id, history_id, seq? }` |
| `geometry_restored` | `{ event, feature_id, history_id, seq? }` |

### Presence

| Event | Payload |
|-------|---------|
| `user_joined` | presence payload |
| `user_left` | presence payload |
| `presence_changed` | presence payload |
| `presence_snapshot` | presence payload |
| `presence_viewport` | presence payload |

### Ephemeral (no seq)

| Event | Payload |
|-------|---------|
| `ephemeral_position` | `{ event, entity_type, entity_id, lon, lat, contractor_id? }` |
| `ephemeral_token_radius` | `{ event, entity_id, radius_m, contractor_id? }` |
| `ephemeral_plant_radius` | `{ event, entity_id, working_radius_m, inactive_radius_m, contractor_id? }` |
| `ephemeral_plant_arc` | `{ event, entity_id, arc_start_deg, arc_end_deg, contractor_id? }` |

### Vertex OT

| Event | Payload |
|-------|---------|
| `vertex_op_applied` | OT payload |
| `vertex_op_ack` | OT payload |

### Permit / Import / Lock

| Event | Payload | Frontend handler |
|-------|---------|------------------|
| `permit_count_updated` | `{ event, permit_id, seq? }` | `PermitService` → reloads permits |
| `bulk_import_completed` | `{ event, created_count, skipped_count, seq? }` | Emitted to `events$` |
| `data_lock_changed` | `{ event, entity_type, entity_id, data, seq? }` | `DataLockService.handleLockChanged` |

### Catch-up response

| Event | Payload |
|-------|---------|
| `catch_up_response` | `{ event, status: "ok" \| "full_reload_required", site_id, current_seq, events? }` |

## Key constants

| Constant | Value |
|----------|-------|
| Heartbeat interval | 30s |
| Missed-pong threshold | 3 |
| Max fast reconnect attempts | 5 |
| Max reconnect delay | 16s |
| Slow reconnect interval | 30s |
| Presence TTL | 15s |
| Event log max events | 5000 |
| Event log TTL | 30min |
| Ephemeral rate-limit interval | ~67ms |
| Max connections per user | 3 |
