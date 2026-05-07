---
service: backend
summary: "LRU clash result cache with generation invalidation"
paths: [backend/app/services/clash/clash_cache.py]
flows: [clash_detect_and_resolve]
touches: []
external: []
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose

Caches computed clash results per site and temporal range, with generation-based
invalidation and debounced background recomputation. Pushes updates to site
subscribers via WebSocket.

## Interface

- `clash_cache.py::clash_cache` — module-level `ClashCache` singleton
- `clash_cache.py::ClashCache.schedule_recomputation(site_id)` → invalidate + debounce
- `clash_cache.py::ClashCache.get_or_compute(session, site_id, query_start, query_end)` → `ClashCacheEntry`
- `clash_cache.py::ClashCache.invalidate_site(site_id)` → None
- `clash_cache.py::ClashCache.invalidate_all()` → None
- `clash_cache.py::derive_entity_severity(results)` → dict[str, str]
- `clash_cache.py::invalidate_clash_cache(site_id)` → None — centralised invalidation; callers import from `services/clash/clash_cache`
- `clash_cache.py::ClashCacheEntry` — dataclass holding `legacy_clashes`, `clash_rule_results`, and `entity_severity`
- 15s server-side timeout on `get_or_compute` via `asyncio.wait_for`; returns 504 on timeout

## State

Runtime state maintained by `clash_cache` singleton.

| symbol | type | semantics |
|---|---|---|
| `_cache` | `OrderedDict[CacheKey, ClashCacheEntry]` | LRU in-memory cache |
| `_generations` | `dict[UUID, int]` | Per-site invalidation counter |
| `_recomputation_tasks` | `dict[UUID, asyncio.Task]` | Debounce timers per site |
| `_compute_locks` | `dict[CacheKey, asyncio.Lock]` | Per-key coalescing: prevents duplicate concurrent computations for same `(site_id, start, end)` |
| `_lock` | `asyncio.Lock` | Protects cache and generation state |

Invariants:
- `_generations[site_id]` monotonically increases
- Cache hit requires `entry.generation == current_gen`, read inside lock → no TOCTOU
- `_recomputation_tasks` entry replaced on every `schedule_recomputation` call
- `_compute_locks` grows with unique cache keys; unbounded (not actively pruned)

## Internals

- Cache key: `(site_id, query_start_iso, query_end_iso)`
- Debounce delay default: 0.5 s
- Per-key compute coalescing: `_compute_locks` prevents N concurrent requests for same key from spawning N computations; first waiter computes, others find fresh cache on re-check
- On miss or stale generation: loads inputs via `_load_clash_inputs`, runs `_compute_clashes_sync` in thread pool via `asyncio.to_thread`
- Resolutions loaded and annotated after computation; unresolved clashes feed `derive_entity_severity`
- Broadcast payload carries BOTH `legacy_clashes` and `clash_rule_results` during ADR D1 deprecation window, plus `entity_severity`
- `_debounced_recompute` opens fresh `async_session_factory()` session — NOT the request session
- `invalidate_clash_cache` was previously duplicated in `entity_broadcast.py` and `feature_broadcast.py`; now consolidated here
- Empty rule set still stores empty entry to avoid repeated DB round-trips

## Touches

| resource | how | why |
|---|---|---|
| postgis | Reads via `_load_clash_inputs` inside fresh session | Load rules, entities, resolutions |
| websocket_runtime | `ws_manager.broadcast_to_room(site:{site_id})` | Push `clash_results_updated` |

## Gotchas

- Debounced recompute fires after request returns; uses independent session
- Cache miss on empty rule set still stores an empty entry
- Resolved clashes excluded from `entity_severity` but included in broadcast payload
- Push path ignores query range because clients may view different ranges
- `_compute_locks` dictionary grows with unique cache keys; consider `WeakValueDictionary` if memory becomes a concern
- 15s timeout frees the request session promptly but the OS thread continues running until `asyncio.to_thread` completes
