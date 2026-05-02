---
service: backend
summary: "WebSocket connection registry, room broadcasting, and presence"
paths: [backend/app/core/websocket_manager.py, backend/app/core/presence_manager.py, backend/app/core/websocket_events.py]
flows: []
touches: [infra/data-stores]
external: [redis]
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Manage WebSocket client connections, route events to site-scoped rooms, enforce
per-connection permission filtering, and track real-time user presence.

## Interface
- `core/websocket_manager.py::WebSocketManager` — Singleton; connection registry, room subscriptions, broadcast fanout
- `core/websocket_manager.py::ws_manager` — Global instance
- `core/websocket_manager.py::WebSocketConnection` — Per-client state: rooms, cached role, contractor_id, can_view_others
- `core/websocket_manager.py::SubscriptionContext` — Pre-fetched permission data passed to `subscribe()`
- `core/websocket_manager.py::WebSocketManager.connect(websocket, user)` → connection_id
- `core/websocket_manager.py::WebSocketManager.disconnect(connection_id)` → None
- `core/websocket_manager.py::WebSocketManager.subscribe(connection_id, room, user, subscription_ctx)` → None
- `core/websocket_manager.py::WebSocketManager.broadcast_to_room(room, event)` → int (recipients)
- `core/websocket_manager.py::WebSocketManager.broadcast_entity_event(site_id, event_type, entity_type, entity_id, data, delta)` → int
- `core/websocket_manager.py::WebSocketManager.broadcast_ephemeral(room, event)` → int
- `core/websocket_manager.py::WebSocketManager.relay_from_redis(room, event)` → int
- `core/websocket_manager.py::WebSocketManager.invalidate_subscription_context(site_id)` → int
- `core/websocket_manager.py::WebSocketManager.invalidate_user_context(user_id, site_id)` → int
- `core/presence_manager.py::PresenceManager` — In-memory presence registry with optional Redis mirror
- `core/presence_manager.py::PresenceInfo` — User presence state in a room
- `core/websocket_events.py::WebSocketEventType` — Union of all event names the backend may publish
- `core/websocket_events.py::EntityEventType`, `PresenceEventType`, `EphemeralEventType`, etc. — Domain-specific event subsets

## State
Runtime state maintained by `WebSocketManager` singleton.

| symbol | type | semantics |
|---|---|---|
| `_lock` | `asyncio.Lock` | Protects all mutable internal state |
| `connections` | `dict[str, WebSocketConnection]` | Active connections keyed by connection_id |
| `rooms` | `dict[str, set[str]]` | Room name → set of connection_ids |
| `_connection_counter` | `int` | Monotonically increasing ID generator |
| `_broadcast_timestamps` | `deque[float]` | Rolling 3600-entry list for broadcasts-per-minute |
| `_presence_mgr` | `PresenceManager` | Delegated presence tracker |
| `_ephemeral_rate_limits` | `dict[str, float]` | `"{conn_id}:{entity_id}" → last_send_time` |
| `MAX_CONNECTIONS_PER_USER` | `int` | 3 |

Per-connection cached fields (set at subscribe time, NEVER auto-refreshed):

| field | type | semantics |
|---|---|---|
| `site_role` | `SiteRole \| None` | Cached role for the subscribed site |
| `site_contractor_id` | `UUID \| None` | Cached contractor ID for the subscribed site |
| `can_view_others` | `dict` | Cached visibility flags (`workers`, `plant`, `zones`) |
| `verified_sites` | `set[str]` | Site IDs that passed access verification; short-circuits re-subscribe |
| `last_pong` | `datetime` | UTC timestamp of last client ping |

Invariants:
- `connection_id in connections` ↔ connection is active
- `connection_id in rooms[room]` → `room in conn.rooms`
- Presence keyed uniquely by `"{user_id}:{room}"`
- Oldest connection evicted silently when user exceeds `MAX_CONNECTIONS_PER_USER`
- Lock held for state mutations; sends happen outside lock to avoid blocking I/O

## Internals
- `connect` evicts oldest connection if user exceeds per-user cap; eviction triggers `user_left` broadcast
- `subscribe` caches `SubscriptionContext` fields on the connection so `_filter_event_for_user` runs without DB access
- `broadcast_to_room` assigns monotonic sequence number via `event_log`, publishes to Redis pub/sub if active, then sends to local subscribers
- `relay_from_redis` does NOT log or re-publish; applies local invalidation and forwards to local subscribers
- `_send_to_local_subscribers` pre-serializes JSON once and fans out concurrently via `asyncio.gather`
- `_filter_event_for_user` applies audience directive first (`owner_or_shared`, `non_owner`), then role/contractor filtering
- Audience directive overrides role bypasses — even superadmins respect privacy directives
- Member/Viewer roles see own contractor's entities plus others if `can_view_others_*` flag is true
- `entity_type == "delivery"` piggybacks on `workers` visibility toggle
- `broadcast_ephemeral` is local-only, no sequence number, no event log, drops silently above ~15 events/sec per `(connection, entity)`
- `invalidate_subscription_context` broadcasts `context_invalidated` to force clients to re-subscribe and refresh cached permissions
- `invalidate_user_context` sends user-scoped `context_invalidated`; must be called once per site for User-level mutations because there is no global per-user channel
- `close_idle_connections` uses close code 1001 and sweeps stale presence
- Redis presence errors are logged and swallowed; in-memory state remains authoritative

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | SQLModel select on `SiteMembership` | Pre-fetch `SubscriptionContext` at subscribe time |
| external/redis | Pub/sub relay, presence mirror, event log | Cross-process broadcast and shared ephemeral state |
| core/event_log | Append sequenced events | Catch-up replay for reconnecting clients |

## Gotchas
- Cached permission fields (`site_role`, `site_contractor_id`, `can_view_others`) are set at subscribe time and NEVER auto-refreshed
- When removing a `SiteMembership`, call `invalidate_user_context` **before** deleting the row
- `broadcast_ephemeral` does NOT publish to Redis; in multi-process deployments ephemeral events only reach local subscribers
- Unknown audience types in `_audience_admits` fail closed (return False), silently dropping events
- Per-user connection limit of 3 silently closes the oldest tab
