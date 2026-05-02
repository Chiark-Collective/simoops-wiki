---
service: backend
summary: "Proximity engine, spatial predicates, and entity colour state"
paths: [
  backend/app/services/clash/proximity.py,
  backend/app/engine/predicates.py,
  backend/app/engine/adapters.py,
]
flows: []
touches: []
external: []
last_verified_commit: TBD
---

# Clash Proximity

## Purpose

Compute per-token colour states (green/amber/red) from spatial proximity to
plant drop zones, zone polygons, and other tokens. Provides the predicate
algebra and entity adapters that drive both legacy colour state and the
declarative clash engine.

## Interface

- `proximity.py::compute_colour_state(session, token, site)` → `(colour, distance)`
- `proximity.py::compute_colour_state_batch(context, tokens)` → `dict[UUID, (colour, distance)]`
- `proximity.py::ColourStateContext.create(session, site, query_start, query_end)` → `ColourStateContext`
- `proximity.py::workers_to_read_batch(session, workers, site, query_start, query_end)` → list[`WorkerRead`]
- `proximity.py::workers_to_read_lite(workers)` → list[`WorkerRead`]
- `proximity.py::worker_to_read(session, worker, site)` → `WorkerRead`
- `predicates.py::SpatialPredicate.intersects` / `contains` / `touches` / `within_distance(threshold)`
- `predicates.py::TemporalPredicate.overlaps_time` / `during_time`
- `predicates.py::LevelPredicate.same_level` / `adjacent_level` / `any_level`
- `predicates.py::ContractorPredicate.different_contractor` / `same_contractor`
- `predicates.py::ProtectionPredicate.exposed_to_crane`
- `predicates.py::PredicateRegistry.get(name)` / `create(name, *args)` / `resolve(spec)`
- `adapters.py::WorkerEntity(token, building_lookup)` — token adapter with overhead exposure
- `adapters.py::PlantEntity(plant)` — plant adapter with drop-zone geometry
- `adapters.py::InactivePlantEntity(plant_read)` — parked plant adapter
- `adapters.py::GeometadataFeatureEntity(feature, layer)` — feature adapter with road buffering

## State

None at module level. `ColourStateContext` is a transient compute context.

## Internals

- 3-priority algorithm in `_check_colour_priority`:
  1. RED: token circle intersects any plant drop zone (gated by level + time)
  2. AMBER: token circle intersects any zone polygon (floor-agnostic)
  3. NEAREST: edge distance to other tokens vs site amber/red thresholds
- `_levels_conflict` treats `None` as level 0; different levels do not clash
- `_times_overlap` handles overnight ranges (e.g., 22:00–06:00) by splitting into two ranges
- Same-contractor exemption skips token-token checks when `exempt_token_token=True`
- `ColourStateContext` pre-loads plant drop zones and zone polygons to avoid N+1 queries
- `workers_to_read_batch` derives colour from `clash_cache.entity_severity` instead of recomputing
- `WorkerEntity.geometry` buffers point by `radius_m` scaled at latitude via `get_scale_factor_at_y`
- `WorkerEntity._compute_overhead_exposure` returns `False` (protected) when worker level < `building.top_concrete_level`
- `PlantEntity.geometry` delegates to `plant_geometry.get_drop_zone_from_plant` (scaled sectors)
- `InactivePlantEntity.geometry` buffers point by `inactive_radius_m`
- `GeometadataFeatureEntity.geometry` buffers road LineStrings by half width with flat end caps
- `PredicateRegistry` maps names to singletons (`intersects`, `same_level`, etc.) and factories (`within_distance`, `kinds`, `types`)
- `ComposedPredicate.all_of` / `any_of` flatten single-item lists to the inner predicate directly

## Touches

| resource | how | why |
|---|---|---|
| [clash_detection](clash_detection.md) | `clash_cache.get_or_compute` | Batch worker colour derivation |
| [clash_engine](clash_engine.md) | `DeclarativeClashEngine.evaluate` | Engine consumes these predicates/adapters |

## Gotchas

- `within_distance` threshold is in EPSG:3857 map units; real-world meters require latitude scale factor
- `compute_colour_state` issues multiple DB queries; use `compute_colour_state_batch` for N>1
- `exposed_to_crane` checks entity A only; typical rule pairs it with a crane-related entity B filter
- Road buffering uses default 7m width when `properties.defaultWidth` is absent
- `GeometadataFeatureEntity` returns empty `Polygon()` when geometry parsing fails — may produce false negatives
