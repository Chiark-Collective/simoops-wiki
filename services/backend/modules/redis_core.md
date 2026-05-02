---
service: backend
summary: "Redis pub/sub relay, presence store, and event log"
paths: [backend/app/core/redis_pubsub.py, backend/app/core/redis_state.py]
flows: []
touches: []
external: [redis]
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Enable cross-process WebSocket broadcast relay, shared presence tracking, and
persistent event logging using Redis.

## Interface
- `core/redis_pubsub.py::RedisPubSub` — Pub/sub adapter; singleton `redis_pubsub`
- `core/redis_pubsub.py::RedisPubSub.start(redis_url)` → None
- `core/redis_pubsub.py::RedisPubSub.stop()` → None
- `core/redis_pubsub.py::RedisPubSub.publish(room, event)` → None
- `core/redis_state.py::RedisPresenceStore` — Hash-based presence with per-field TTL emulation
- `core/redis_state.py::RedisPresenceStore.set_presence(room, user_id, info)` → None
- `core/redis_state.py::RedisPresenceStore.remove_presence(room, user_id)` → None
- `core/redis_state.py::RedisPresenceStore.heartbeat(room, user_id)` → None
- `core/redis_state.py::RedisPresenceStore.get_room_presence(room)` → List[dict]
- `core/redis_state.py::RedisEventLog` — Sorted-set ring buffer with atomic sequence
- `core/redis_state.py::RedisEventLog.log_event(room, event)` → int (sequence number)
- `core/redis_state.py::RedisEventLog.get_events_since(room, last_seq)` → List[dict] | None
- `core/redis_state.py::RedisEventLog.current_seq(room)` → int
- `core/redis_state.py::RedisEventLog.clear()` → None

## State
Redis keyspace managed by this module.

| key pattern | type | semantics |
|---|---|---|
| `simoops:broadcast:{room}` | Pub/sub channel | Cross-process WS broadcast relay |
| `simoops:presence:{room}` | Redis Hash | `user_id → JSON presence info` |
| `simoops:presence:{room}:{user_id}:ttl` | Redis String (EXPIRE) | Companion key emulating per-field Hash TTL |
| `simoops:events:{room}` | Redis Sorted Set | `score=seq, member=JSON log entry` |
| `simoops:seq:{room}` | Redis String (counter) | Atomically incremented for monotonic sequence |

Runtime objects:

| symbol | type | semantics |
|---|---|---|
| `redis_pubsub._redis` | `aioredis.Redis \| None` | Async Redis client |
| `redis_pubsub._pubsub` | `aioredis.client.PubSub \| None` | Pub/sub connection handle |
| `redis_pubsub._listener_task` | `asyncio.Task \| None` | Background message loop |
| `redis_pubsub._running` | `bool` | Lifecycle flag |
| `_PROCESS_ID` | `str` | Immutable `proc_{pid}_{uuid8}`; set once at import |

Invariants:
- `_PROCESS_ID` never changes for the lifetime of the process
- Self-echo prevention: listener drops messages where `_origin == _PROCESS_ID`
- Event log Lua script performs `INCR`, `ZADD`, `ZREMRANGEBYRANK` atomically

## Internals
- Pub/sub uses a single pattern subscription (`psubscribe simoops:broadcast:*`) for all rooms
- Listener loop uses `get_message(timeout=1.0)` to remain cancellable on shutdown
- `_PROCESS_ID` fuses PID and UUID fragment to survive process forks and module reloads
- `publish` logs a warning once per lost transition if `_redis` is None while `_running` is true
- Presence uses companion TTL keys because Redis Hashes do not support per-field expiration
- `get_room_presence` verifies companion TTL key existence and lazily prunes expired hash fields
- `RedisEventLog` Lua script embeds sequence number via Lua string concatenation (O(1), no JSON parse in Redis)
- `get_events_since` returns `None` (not `[]`) when gap is too large, signaling caller to request full sync
- `get_events_since` filters by wall-clock age on read without removing expired entries from Redis
- `clear()` deletes all matching keys globally via `scan_iter`; intended for testing only

## Touches
| resource | how | why |
|---|---|---|
| external/redis | Pub/sub, Hash, String, Sorted Set, Lua scripts | Cross-process relay, presence, event log |
| core/websocket_manager | Relay target for inbound Redis broadcasts | `ws_manager` imported lazily inside listener |
| core/event_log | Imports `DEFAULT_MAX_EVENTS` and `DEFAULT_TTL_SECONDS` | Shared defaults for in-memory and Redis backends |

## Gotchas
- Pub/sub listener does **not** auto-reconnect; if Redis drops, listener exits and stays dead until `start()` is called again
- `publish` silently returns if `_redis` is None; cross-worker broadcasts may be lost during transient disconnects
- `get_room_presence` issues `EXISTS` per user, making it O(N) in room size
- Presence hash fields can become orphaned if process crashes; companion TTL key eventually expires, but hash field persists until pruned
- Event log is trimmed by count (`max_events`) on write, not by TTL; stale events remain until aged out of count window
- `get_events_since` returning `None` vs `[]` is semantically critical: `None` = "too far behind, full sync needed"; `[]` = "fully caught up"
- `clear()` has no production guardrails
