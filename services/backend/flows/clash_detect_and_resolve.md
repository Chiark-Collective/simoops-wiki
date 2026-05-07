---
trigger: { channel: websocket, ref: "entity_created or entity_updated event" }
services: [backend]
contracts: []
external: []
---

# Clash Detect and Resolve

## Trigger

WebSocket `entity_created` or `entity_updated` event, or HTTP POST to
`/api/clash-rules/{id}/evaluate`. Both paths are gated by RBAC.

## Steps

1. HTTP route handler or WebSocket event handler receives trigger
2. For WebSocket mutations: calls `clash_cache.schedule_recomputation(site_id)`
3. `schedule_recomputation` increments per-site generation, cancels existing
   debounce timer, and starts a new `_debounced_recompute` task
4. After `DEFAULT_RECOMPUTATION_DELAY` (0.5 s), `_debounced_recompute` opens
   a fresh `async_session_factory()` session
5. Calls `clash_cache.get_or_compute(session, site_id)` — full site, no
   temporal range filter
6. `get_or_compute` checks cache generation inside `asyncio.Lock`; on miss or
   stale generation calls `_load_clash_inputs`
7. `_load_clash_inputs` loads site, active profile, enabled rules, tokens,
   plants, clashable features, inactive cranes, and building features; expunges
   all ORM objects from the session
8. Runs `_compute_clashes_sync` in a thread pool via `asyncio.to_thread`
9. `_compute_clashes_sync` wraps entities with adapters, compiles rules,
   evaluates via `DeclarativeClashEngine`, formats results with
   `ClashResultFormatter`, and applies same-contractor exemptions
10. Back in `get_or_compute`: loads resolutions, annotates clashes with
    `resolved` flags, filters unresolved for severity derivation
11. `derive_entity_severity` computes per-entity worst-case severity from
    unresolved `ClashRuleResult`s
12. Stores `ClashCacheEntry` (legacy + canonical shapes) in the LRU cache
13. `_debounced_recompute` broadcasts `clash_results_updated` to WebSocket
    room `site:{site_id}` via `ws_manager`
14. HTTP POST path bypasses cache: calls `generate_clash_list` directly,
    which follows steps 7–9 and returns legacy clashes immediately

## Side effects

- PostGIS reads (rules, entities, features, resolutions)
- In-memory cache write (`ClashCache._cache`)
- Per-key compute coalescing via `_compute_locks` prevents duplicate concurrent computations
- 15s `asyncio.wait_for` timeout on `GET /api/clashes`; returns 504 on exceed
- WebSocket broadcast to `site:{site_id}` room (via `websocket_runtime` → `redis_core` relay)
- Audit log entry for manual rule evaluations
- `clash_resolution` table INSERT/UPDATE when resolving/unresolving clashes

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| Rule compilation error | Exception in `RuleCompiler` | Logged; rule skipped; evaluation continues |
| Empty entity set | No entities in shift | Returns `[]`; no broadcast |
| Cache stale | Generation mismatch on read | Recompute from scratch |
| Debounce timer cancelled | New mutation within 0.5 s | Timer resets; only last mutation triggers compute |
| Recompute failure | Exception in `_debounced_recompute` | Logged; pending task reference cleaned up; clashes remain stale |
| Compute timeout | `asyncio.TimeoutError` on >15s computation | Returns 504 Gateway Timeout; connection returned to pool cleanly via session rollback shielding |
| Cache miss (key) | `_compute_locks` coalescing miss | Subsequent request finds stale entry and triggers recomputation |
| Resolution not found | `unresolve_clash` miss | Returns `UnresolveResult(deleted=False)` |
