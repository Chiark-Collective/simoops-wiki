---
service: ui
summary: Generic reactive store, CRUD facade, API wrappers, and core entity types.
paths:
  - src/app/services/entity-store.ts
  - src/app/services/entity.service.ts
  - src/app/services/entity-operations.service.ts
  - src/app/api.service.ts
  - src/app/api/area.api.ts
  - src/app/api/worker.api.ts
  - src/app/api/plant.api.ts
  - src/app/api/site.api.ts
  - src/app/api/auth.api.ts
  - src/app/api/clash.api.ts
  - src/app/api/geometry.api.ts
  - src/app/api/planning.api.ts
  - src/app/api/report.api.ts
  - src/app/api/revision.api.ts
  - src/app/api/weather.api.ts
  - src/app/api/export.api.ts
  - src/app/api/geometadata.api.ts
  - src/app/api/entity-support.api.ts
  - src/app/types/entity.types.ts
  - src/app/types/entity-kind.ts
  - src/app/services/data-load.service.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Centralised state and API layer for spatial entities. `EntityStore` provides a per-type reactive collection; `EntityService` orchestrates load, CRUD, optimistic updates, conflict handling, and WebSocket sync. Domain API services translate between backend endpoints and frontend types. `EntityOperationsService` offers a single dispatch table for kind-agnostic operations.

## Interface
- `services/entity-store.ts::EntityStore` — Generic `BehaviorSubject` store with O(1) index, supporting add, remove, update, patch, merge, replace, and batch operations.
- `services/entity.service.ts::EntityService` — CRUD facade for workers, plants, and areas; manages loading state, optimistic updates, 409 conflict events, and WebSocket delta application.
- `services/entity-operations.service.ts::EntityOperationsService` — Per-kind dispatch for delete, setLocked, and centerPoint via `dispatchByKind`.
- `api.service.ts::ApiService` — Facade that delegates to all domain API services.
- `api/worker.api.ts::WorkerApi` — Token CRUD, schedule groups, copy-from-range, batch delete, and restore.
- `api/plant.api.ts::PlantApi` — Plant CRUD, schedule groups, copy-from-range, position-group delete, and restore.
- `api/area.api.ts::AreaApi` — Area CRUD, schedule groups, copy-from-range, restore, and `GeometadataFeature` mapping.
- `api/site.api.ts::SiteApi` — Sites, shifts, contractors, site maps, label styles, data locks, and site nuke.
- `api/auth.api.ts::AuthApi` — Current user, password change, invites, invite links, and pending memberships.
- `api/clash.api.ts::ClashApi` — Clash listing, resolution, rule CRUD, versioning, DSL, and rule profiles.
- `api/geometry.api.ts::GeometryApi` — Cut holes, undo cuts, overlap checks, geometry history, and layer type rules.
- `api/planning.api.ts::PlanningApi` — Planning cycle CRUD, contractor submissions, actualization, compare, and carry-forward.
- `api/report.api.ts::ReportApi` — Report templates, sessions, auto-save, and PDF/DOCX export.
- `api/revision.api.ts::RevisionApi` — Per-type `/at-time` endpoints and `loadRevision` fan-out.
- `api/weather.api.ts::WeatherApi` — Weather timeline for the ribbon.
- `api/export.api.ts::ExportApi` — GeoJSON export, permit upload, listing, and entity creation from permits.
- `api/geometadata.api.ts::GeometadataApi` — Layer CRUD, feature CRUD, building lookups, floor plans, and bundle import.
- `api/entity-support.api.ts::EntitySupportApi` — Roads, deliveries, PoIs, text labels, smart groups, alerts, and bulk import.
- `types/entity.types.ts::Worker` — Token entity with position, radius, temporal bounds, building placement, and plan state.
- `types/entity.types.ts::Plant` — Plant entity with working radius, arc angles, inactive footprint, and schedule group.
- `types/entity.types.ts::Area` — Area entity with polygon, feature type, clashable flag, and temporal bounds.
- `types/entity.types.ts::DomainEntity` — Union of `Worker | Plant | Area`.
- `types/entity-kind.ts::DomainEntityKind` — Discriminator literal `'worker' | 'plant' | 'area'`.
- `services/data-load.service.ts::DataLoadService` — Centralised orchestrator for all entity reloads: tokens, plants, areas, roads, deliveries, POIs, alerts, text labels, geometadata, sun times, and planning cycle data.
