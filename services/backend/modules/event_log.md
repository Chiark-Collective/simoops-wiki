---
service: backend
summary: "In-memory per-room event log with ring buffers"
paths: [backend/app/core/event_log.py]
flows: []
touches: []
external: []
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Provide sequenced, in-memory event logging per room to enable incremental
WebSocket catch-up on reconnection instead of full entity reload.

## Interface
- `core/event_log.py::EventLogEntry`
- `core/event_log.py::RoomEventLog`
- `core/event_log.py::RoomEventLog.append` → int (sequence number)
- `core/event_log.py::RoomEventLog.get_events_since` → list[dict] \| None
- `core/event_log.py::EventLog`
- `core/event_log.py::EventLog.get_room` → RoomEventLog
- `core/event_log.py::EventLog.log_event` → int
- `core/event_log.py::EventLog.get_events_since` → list[dict] \| None
- `core/event_log.py::EventLog.current_seq` → int
- `core/event_log.py::EventLog.clear` → None
- `core/event_log.py::event_log` — Module-level singleton

## State
Per-room ring buffers with monotonic sequence counters.

| symbol | type | semantics |
|---|---|---|
| `_rooms` | `dict[str, RoomEventLog]` | Lazy-created room logs |
| `_buffer` | `deque[EventLogEntry]` | Ring buffer per room (`maxlen=DEFAULT_MAX_EVENTS`) |
| `_seq_counter` | `int` | Monotonically increasing per room |
| `DEFAULT_MAX_EVENTS` | `int` | 5000 |
| `DEFAULT_TTL_SECONDS` | `float` | 1800.0 (30 minutes) |

Invariants:
- `_seq_counter` increases monotonically within a process lifetime
- `append` injects `seq` into the event dict for client-side dedup
- `get_events_since` returns `None` (not `[]`) when `last_seq` is older than the
  oldest retained entry → signals full reload required

## Internals
- `EventLog` is a module-level singleton (`event_log`)
- All methods are `async` to present a uniform interface with
  `core/redis_state.py::RedisEventLog`, but perform no I/O
- `RoomEventLog` uses `collections.deque(maxlen=DEFAULT_MAX_EVENTS)` for
  automatic eviction by count
- TTL pruning is lazy: `_prune_expired` runs on `get_events_since` before
  returning results
- Events are NOT persisted across process restarts; reconnecting clients with a
  stale `last_seq` receive `None` and trigger a full reload
- `get_events_since(room, 0)` on a fresh room returns `[]` (fully caught up)
- `get_events_since(room, N)` where `N > current_seq` returns `[]`

## Touches
| resource | how | why |
|---|---|---|
| core/redis_state.py | `RedisEventLog` mirrors this interface with Redis persistence | Durable, cross-process event log alternative |

## Gotchas
- `None` vs `[]` from `get_events_since` is semantically critical: `None` = gap
  too large, full reload needed; `[]` = fully caught up
- Process restart resets all sequence counters to 0; all reconnecting clients
  will perform full reloads
- Ring buffer evicts by count, not by TTL; stale events remain until pushed out
  by newer events
- `clear()` deletes all room logs; intended for testing only
