---
service: backend
summary: "Redis pub/sub relay, presence store, and event log"
paths: [backend/app/core/redis_pubsub.py, backend/app/core/redis_state.py]
flows: []
touches: []
external: [redis]
last_verified_commit: b8ea3ec5
---

## Purpose
Enable cross-process WebSocket broadcast relay, shared presence tracking, and
persistent event logging using Redis.

## Interface
- `core/redis_pubsub.py::RedisPubSub` — Pub/sub adapter; singleton `redis_pubsub`
- `core/redis_pubsub.py::RedisPubSub.start(redis_url)` → None
- `core/redis_pubsub.py::RedisPubSub.stop()` → None
- `core/redis_pubsub.py::RedisPubSub.publish(room, event)` → None
- `core/redis_pubsub.py::RedisPubSub.is_healthy` → bool
- `core/redis_pubsub.py::RedisPubSub.dropped_count` → int
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
| `simoops:{env}:broadcast:{room}` | Pub/sub channel | Cross-process WS broadcast relay |
| `simoops:{env}:presence:{room}` | Redis Hash | `user_id → JSON presence info` |
| `simoops:{env}:presence:{room}:{user_id}:ttl` | Redis String (EXPIRE) | Companion key emulating per-field Hash TTL |
| `simoops:{env}:events:{room}` | Redis Sorted Set | `score=seq, member=JSON log entry` |
| `simoops:{env}:seq:{room}` | Redis String (counter) | Atomically incremented for monotonic sequence |

Runtime objects:

| symbol | type | semantics |
|---|---|---|
| `redis_pubsub._redis` | `aioredis.Redis \| None` | Async Redis client |
| `redis_pubsub._pubsub` | `aioredis.client.PubSub \| None` | Pub/sub connection handle |
| `redis_pubsub._listener_task` | `asyncio.Task \| None` | Background message loop |
| `redis_pubsub._running` | `bool` | Lifecycle flag |
| `_PROCESS_ID` | `str` | Immutable `proc_{pid}_{uuid8}`; set once at import |
| `redis_pubsub._dropped_count` | `int` | Cumulative dropped broadcasts since process start |
| `redis_pubsub._last_warned_drop` | `int` | Last drop count at which warning was logged |
| `redis_pubsub._messages_since_reconnect` | `int` | Messages processed since last reconnect; drives backoff reset |

Invariants:
- `_PROCESS_ID` never changes for the lifetime of the process
- Self-echo prevention: listener drops messages where `_origin == _PROCESS_ID`
- Event log Lua script performs `INCR`, `ZADD`, `ZREMRANGEBYRANK` atomically

## Internals
- Pub/sub uses a single pattern subscription (`psubscribe simoops:broadcast:*`) for all rooms
- `_listen_loop` uses `get_message(timeout=1.0)` to remain cancellable on shutdown; `_listen` supervises it with exponential backoff (1s→60s) and retry
- `_PROCESS_ID` fuses PID and UUID fragment to survive process forks and module reloads
- `publish` increments `_dropped_count` and logs a warning on a logarithmic schedule (1, 2, 4, 8, …) when `_redis` is None
- `is_healthy` checks listener task liveness (distinct from `is_active`) so readiness probes can cycle a pod with a dead listener
- Presence uses companion TTL keys because Redis Hashes do not support per-field expiration
- `get_room_presence` verifies companion TTL key existence and lazily prunes expired hash fields
- Key prefixes include `settings.environment` so multiple environments can share a Redis instance safely
- `RedisEventLog.clear()` raises in non-test environments; active-env namespace provides structural boundary
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
- Supervisor retry has a minimum 1s blackout; messages arriving during reconnect windows are dropped and counted
- Backoff resets only after the inner loop processes at least one message; a connection that repeatedly fails before receiving any message will max out at 60s intervals
- Dropped broadcasts are counted but not requeued; a long Redis outage will accumulate drops without backpressure on publishers
- `get_room_presence` issues `EXISTS` per user, making it O(N) in room size
- Presence hash fields can become orphaned if process crashes; companion TTL key eventually expires, but hash field persists until pruned
- Event log is trimmed by count (`max_events`) on write, not by TTL; stale events remain until aged out of count window
- `get_events_since` returning `None` vs `[]` is semantically critical: `None` = "too far behind, full sync needed"; `[]` = "fully caught up"
- `clear()` raises in non-test environments but still lacks additional auth guardrails
