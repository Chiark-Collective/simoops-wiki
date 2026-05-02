---
service: backend
summary: "Runtime clash detection, resolution, caching, and at-time evaluation"
paths: [
  backend/app/services/clash/clash_detection_service.py,
  backend/app/services/clash/clash_resolution_service.py,
  backend/app/services/clash/clash_cache.py,
  backend/app/services/clash/clash_at_time_service.py,
  backend/app/services/clash/clash_scene_scoring.py,
  backend/app/services/clash/clash_result_formatter.py,
]
flows: [clash_detect_and_resolve]
touches: []
external: []
last_verified_commit: TBD
---

# Clash Detection

## Purpose

Orchestrate clash detection over live and historical entity sets, persist
resolutions, cache results with generation invalidation, and score spatial
scenes for reporting.

## Interface

- `clash_detection_service.py::generate_clash_list(session, site_id, query_start, query_end)` → list[dict]
- `clash_detection_service.py::_load_clash_inputs(session, site_id, query_start, query_end)` → `ClashInputs | None`
- `clash_detection_service.py::_compute_clashes_sync(inputs)` → `(legacy_clashes, raw_results)`
- `clash_detection_service.py::_get_inactive_cranes_for_clashes(...)` → list[dict]
- `clash_resolution_service.py::resolve_clash(session, site_id, entity_a, entity_b, rule_name, resolved_by, note)` → `ClashResolution`
- `clash_resolution_service.py::unresolve_clash(session, site_id, entity_a, entity_b, rule_name)` → `UnresolveResult`
- `clash_resolution_service.py::get_resolutions_for_site(session, site_id)` → dict
- `clash_resolution_service.py::annotate_clashes_with_resolutions(clashes, resolutions)` → None (mutates)
- `clash_cache.py::clash_cache` — module singleton `ClashCache`
- `clash_cache.py::clash_cache.schedule_recomputation(site_id)` → invalidate + debounce
- `clash_cache.py::clash_cache.get_or_compute(session, site_id, query_start, query_end)` → `ClashCacheEntry`
- `clash_cache.py::derive_entity_severity(results)` → dict[str, str]
- `clash_at_time_service.py::ClashAtTimeService.evaluate(site_id, at_time)` → list[dict]
- `clash_scene_scoring.py::score_and_rank_scenes(clashes, entities, ...)` → list[`ScoredScene`]
- `clash_result_formatter.py::ClashResultFormatter.convert(result, entities_by_id)` → dict
- `clash_result_formatter.py::infer_clash_type(entity_a_type, entity_b_type)` → str

## State

`clash_cache` singleton maintains runtime state.

| symbol | type | semantics |
|---|---|---|
| `_cache` | `OrderedDict[CacheKey, ClashCacheEntry]` | LRU in-memory cache |
| `_generations` | `dict[UUID, int]` | Per-site invalidation counter |
| `_recomputation_tasks` | `dict[UUID, asyncio.Task]` | Debounce timers per site |
| `_lock` | `asyncio.Lock` | Protects cache and generation state |

Invariants:
- `_generations[site_id]` monotonically increases
- Cache hit requires `entry.generation == current_gen` (read inside lock to avoid TOCTOU)
- `_recomputation_tasks` entry replaced on every `schedule_recomputation` call

## Internals

- `_load_clash_inputs` expunges all ORM objects before returning so the session can be released during CPU-bound work
- Inactive cranes synthesized from `Plant` history; active cranes filtered by schedule overlap
- Building features loaded without `plan_state` filter because buildings are physical structures
- `_compute_clashes_sync` is safe for `asyncio.to_thread()` — no session references
- Same-contractor exemptions applied post-detection using `site.same_contractor_exemptions`
- `ClashCache` pushes BOTH `legacy_clashes` and `clash_rule_results` during deprecation window (ADR D1)
- Debounced recompute opens a fresh `async_session_factory()` session — not the request session
- `ClashAtTimeService` reconstructs tokens/plants from audit snapshots, features from `FeatureVersion`
- Rule reconstruction at time T: versioned rules from `clash_rule_versions` + legacy live rules without version history
- Inactive crane split at time T uses ±30 min window around `at_time`
- `score_and_rank_scenes` uses 5-component scoring (severity, cross-contractor, diversity, proximity, temporal)
- Scenes are spatially clustered with greedy haversine distance, then deduplicated by exclusive clash assignment
- Temporal sub-grouping splits scenes by overlapping entity time windows
- `ClashResultFormatter` maps `ClashRuleResult` to legacy clash dicts with type-specific keys

## Touches

| resource | how | why |
|---|---|---|
| [websocket_runtime](websocket_runtime.md) | `ws_manager.broadcast_to_room` | Push `clash_results_updated` to site room |
| [redis_core](redis_core.md) | Via `websocket_runtime` relay | Cross-process broadcast of clash updates |
| [core_rbac](core_rbac.md) | Route-level permission checks | HTTP/WebSocket handlers verify `clash_rule.evaluate` permission |

## Gotchas

- Debounced recompute fires after the request has returned; uses independent session
- Cache miss on empty rule set still stores an empty entry to avoid repeated DB round-trips
- Resolved clashes are excluded from `entity_severity` but included in broadcast payload
- At-time evaluation uses live site config for active profile and exemptions (full reconstruction deferred)
- `_compute_clashes_sync` filters resolved clashes only for severity; legacy list includes them annotated
