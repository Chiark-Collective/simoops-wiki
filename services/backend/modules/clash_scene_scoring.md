---
service: backend
summary: "Spatial clustering and importance scoring for clash scenes"
paths: [backend/app/services/clash/clash_scene_scoring.py]
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose

Clusters clash-involved entities spatially, scores each cluster by multi-factor
importance, and ranks scenes for report context enrichment.

## Interface

- `clash_scene_scoring.py::score_and_rank_scenes(clashes, entities, cluster_radius_m, entity_time_ranges, query_start, query_end)` → list[ScoredScene]
- `clash_scene_scoring.py::cluster_entities(entities, cluster_radius_m)` → list[list[GeoEntity]]
- `clash_scene_scoring.py::GeoEntity` — positioned entity for clustering/scoring
- `clash_scene_scoring.py::ScoredScene` — scored cluster with bounds, tier, reason

## State

None. Pure functions.

## Internals

- 5-component scoring: severity (40%), cross-contractor (20%), diversity (15%), proximity (15%), temporal density (10%)
- `cluster_entities` uses greedy haversine clustering matching frontend `clusterObjects`
- `_score_severity` floors at 10.0 when any red clash present
- Temporal sub-grouping splits scenes by overlapping entity time windows when temporal data provided
- `_deduplicate_scenes` assigns clashes exclusively to highest-scored scene; lower scenes lose shared clashes
- Bounds include entity radius with cos(lat) correction and 10% padding
- Minimum extent enforced at 10 m

## Touches

None.

## Gotchas

- Scoring weights must agree with frontend `ExportService` weights
- `_deduplicate_scenes` uses `id()` of clash dicts for identity — works only when same dict objects passed
- Scene without clashes after dedup is dropped entirely
