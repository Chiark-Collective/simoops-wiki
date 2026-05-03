---
service: backend
summary: "Pluggable report context providers with dependency-aware topological ordering"
paths: [backend/app/services/report/providers/registry.py, backend/app/services/report/providers/base.py, backend/app/services/report/providers/core_context.py, backend/app/services/report/providers/workers_context.py, backend/app/services/report/providers/plants_context.py, backend/app/services/report/providers/clash_context.py, backend/app/services/report/providers/deliveries_context.py, backend/app/services/report/providers/permits_context.py]
flows: []
touches: [postgis]
external: []
last_verified_commit: f9606469ce367229c5c91e03c3ba917779015030
---

## Purpose
Six pluggable context providers enrich a shared dict with domain-specific data for report pre-filling and export. Registration order is derived from declared `requires`/`provides` dependencies via `graphlib.TopologicalSorter`.

## Interface
- `providers/registry.py::PROVIDER_REGISTRY` — ordered dict of all providers in dependency order
- `providers/registry.py::topologically_sort_providers(providers)` → list[ContextProvider] — raise on duplicate key, missing producer, or cycle
- `providers/registry.py::run_providers(providers, session, site_id, user, ...)` → context dict
- `providers/base.py::ContextProvider` — Protocol defining `provider_id`, `is_refreshable`, `requires`, `provides`, `enrich(context, session, ...)`
- `providers/core_context.py::CoreContextProvider` — site, user, date, shift, contractors
- `providers/workers_context.py::TokensContextProvider` — workers with permit extraction
- `providers/plants_context.py::PlantsContextProvider` — equipment/plants
- `providers/clash_context.py::ClashScenesContextProvider` — ranked clash scenes
- `providers/deliveries_context.py::DeliveriesContextProvider` — delivery schedules
- `providers/permits_context.py::PermitsContextProvider` — imported permits

## State
- `PROVIDER_REGISTRY` populated at import time by `_register_providers()`
- Run order derived from `requires`/`provides` edges; no hand-maintained list

Provider dependency graph:

| provider | requires | provides |
|---|---|---|
| `core` | `()` | `site`, `user`, `report_date`, `meeting_date`, `shift`, `contractors`, `_contractor_map`, `_permit_patterns` |
| `tokens` | `_contractor_map`, `_permit_patterns` | `tokens`, `_raw_tokens` |
| `plants` | `_contractor_map` | `plants`, `_raw_plants` |
| `clash_scenes` | `_raw_tokens`, `_raw_plants`, `_contractor_map` | `clashes`, `clash_scenes` |
| `deliveries` | `_contractor_map` | `deliveries` |
| `permits` | `()` | `permits`, `permit_summary` |

## Internals
- `is_refreshable` flag: `True` for live data (core, tokens, plants, clash_scenes); `False` for snapshot data (deliveries, permits)
- `topologically_sort_providers` raises `ValueError` on: duplicate provider for same key, missing required producer, cycle among providers
- `CoreContextProvider` sets `_contractor_map` and `_permit_patterns` for downstream use
- `TokensContextProvider` extracts permit numbers via regex from worker labels using `_permit_patterns`
- `PlantsContextProvider` filters plants by temporal overlap with query range
- `ClashScenesContextProvider` runs clash detection engine, builds `GeoEntity` list, scores scenes via `score_and_rank_scenes`
- `DeliveriesContextProvider` supports `delivery_lookahead_days` for multi-day ranges beyond the shift window
- `PermitsContextProvider` groups permits by contractor and adds `permit_summary` stats
- Provider failures are logged and skipped; context remains partial

## Touches
| Resource | How | Why |
|---|---|---|
| postgis | SQLModel | Site, worker, plant, delivery, permit queries |

## Gotchas
- Missing `_contractor_map` → tokens/plants lose contractor names
- Missing `_permit_patterns` → permit extraction falls back to empty strings
- `ClashScenesContextProvider` requires `_raw_tokens` and `_raw_plants` from earlier providers
