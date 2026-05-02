---
service: backend
summary: "WebSocket presence state machine"
paths: [backend/app/core/presence_manager.py]
flows: []
touches: []
external: [redis]
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Track real-time user presence in site rooms: who is online, what they are
editing, and where they are viewing. Returns broadcast events without coupling
to WebSocket transport.

## Interface
- `core/presence_manager.py::PresenceInfo`
- `core/presence_manager.py::PresenceManager`
- `core/presence_manager.py::PresenceManager.join` → dict | None
- `core/presence_manager.py::PresenceManager.leave` → dict | None
- `core/presence_manager.py::PresenceManager.cleanup_redis_presence` → None
- `core/presence_manager.py::PresenceManager.prune_stale` → list[tuple]
- `core/presence_manager.py::PresenceManager.update_editing` → dict | None
- `core/presence_manager.py::PresenceManager.update_viewport` → dict | None
- `core/presence_manager.py::PresenceManager.refresh_ttl` → None
- `core/presence_manager.py::PresenceManager.get_room_presence` → list[dict]

## State
Runtime presence state maintained in-memory with optional Redis mirror.

| symbol | type | semantics |
|---|---|---|
| `presence` | `dict[str, PresenceInfo]` | In-memory registry keyed by `"{user_id}:{room}"` |
| `_redis_presence` | `RedisPresenceStore \| None` | Cross-process presence mirror |

Invariants:
- `presence_key in presence` → user is considered online in that room
- `(now - last_heartbeat) > PRESENCE_TTL_SECONDS` → entry is stale and eligible for pruning
- Local entries take precedence over Redis entries in `get_room_presence`
- Redis errors are logged and swallowed; in-memory remains source of truth

## Internals
- `join` returns a `user_joined` event only if the user was not already present
- `leave` is synchronous so it can be called under an `asyncio.Lock` without
  holding the lock across I/O
- Redis cleanup after `leave` is the caller's responsibility via
  `cleanup_redis_presence` (must run after the lock is released)
- `prune_stale` is a safety net for idle connections that never explicitly
  disconnect (background tabs, sleeping devices)
- `update_editing` emits `presence_changed`; `update_viewport` emits
  `presence_viewport` (ephemeral)
- `refresh_ttl` updates `last_heartbeat` without broadcasting; also forwards
  heartbeat to Redis if configured
- `get_room_presence` prunes stale local entries, then merges Redis entries
  for users not present locally
- `PRESENCE_TTL_SECONDS` is 15.0

## Touches
| resource | how | why |
|---|---|---|
| external/redis | Hash + companion TTL keys via `RedisPresenceStore` | Cross-process presence sharing |
| core/websocket_manager | Calls `join`, `leave`, `broadcast` of returned events | Connection lifecycle and event fanout |

## Gotchas
- `leave` does NOT clean Redis; caller must call `cleanup_redis_presence`
  afterward or the user remains visible to other processes
- Stale entries are only pruned on `get_room_presence` or `prune_stale` sweep;
  without either, idle users appear online indefinitely
- `update_editing` and `update_viewport` silently return `None` if the user is
  not in the room (e.g., race between join and state update)
- Redis mirror is optional; single-process deployments run with in-memory only
