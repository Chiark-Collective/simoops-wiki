---
service: backend
summary: "Pluggable report context providers: site, workers, plants, clashes, deliveries, permits"
paths: [backend/app/services/report/providers/registry.py, backend/app/services/report/providers/base.py, backend/app/services/report/providers/core_context.py, backend/app/services/report/providers/workers_context.py, backend/app/services/report/providers/plants_context.py, backend/app/services/report/providers/clash_context.py, backend/app/services/report/providers/deliveries_context.py, backend/app/services/report/providers/permits_context.py]
flows: []
touches: [postgis]
external: []
last_verified_commit: TBD
---

# Report Providers

## Purpose
Six pluggable context providers enrich a shared dict with domain-specific data for report pre-filling and export. Registration order is invariant because later providers read keys set by earlier ones.

## Interface
- `providers/registry.py::PROVIDER_REGISTRY` — ordered dict of all providers
- `providers/registry.py::run_providers(providers, session, site_id, user, ...)` → context dict
- `providers/base.py::ContextProvider` — Protocol defining `provider_id`, `is_refreshable`, `enrich(context, session, ...)`
- `providers/core_context.py::CoreContextProvider` — site, user, date, shift, contractors
- `providers/workers_context.py::TokensContextProvider` — workers with permit extraction
- `providers/plants_context.py::PlantsContextProvider` — equipment/plants
- `providers/clash_context.py::ClashScenesContextProvider` — ranked clash scenes
- `providers/deliveries_context.py::DeliveriesContextProvider` — delivery schedules
- `providers/permits_context.py::PermitsContextProvider` — imported permits

## State
- `PROVIDER_REGISTRY` populated at import time by `_register_providers()`
- Registration order invariant: core → tokens → plants → clash_scenes → deliveries → permits

## Internals
- `is_refreshable` flag: `True` for live data (core, tokens, plants, clash_scenes); `False` for snapshot data (deliveries, permits)
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
