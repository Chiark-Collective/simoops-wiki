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
flows:
  - entity-crud
  - optimistic-update
  - conflict-resolution
  - context-loading
  - websocket-sync
  - schedule-group
  - revision-mode
touches:
  - http
  - websocket
  - rxjs
external:
  - angular/core
  - angular/common/http
  - rxjs
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Centralised reactive state and API layer for spatial entities. `EntityStore` provides a per-type `BehaviorSubject` collection with O(1) index. `EntityService` orchestrates load, CRUD, optimistic updates, 409 conflict events, and WebSocket delta application. Domain API services translate backend endpoints to frontend types. `EntityOperationsService` offers a single `dispatchByKind` table for kind-agnostic operations. `DataLoadService` centralises the reactive loading pipeline for all entity types.

## Interface
- `services/entity-store.ts::EntityStore` — Generic store with `BehaviorSubject<T[]>`, O(1) index, loading flag, loaded-once flag. Supports `add`, `remove`, `update`, `patch`, `merge`, `replace`, `batchUpdate`, `batchAdd`, `batchRemove`, `removeWhere`.
- `services/entity.service.ts::EntityService` — CRUD facade for workers, plants, areas. Manages loading state, optimistic updates, 409 conflicts, WebSocket sync, tombstones, and local state manipulation for undo/redo.
- `services/entity-operations.service.ts::EntityOperationsService` — Per-kind dispatch for `delete`, `setLocked`, `centerPoint` via `dispatchByKind`.
- `api.service.ts::ApiService` — Facade delegating to all domain API services. Exposes `scheduleGroupApi` per `DomainEntityKind`.
- `api/worker.api.ts::WorkerApi` — Token CRUD, schedule groups, copy-from-range, batch delete, restore.
- `api/plant.api.ts::PlantApi` — Plant CRUD, schedule groups, copy-from-range, position-group delete, restore.
- `api/area.api.ts::AreaApi` — Area CRUD, schedule groups, copy-from-range, restore, and `mapFeatureToArea` translation.
- `api/site.api.ts::SiteApi` — Sites, shifts, contractors, site maps, label styles, data locks, site nuke.
- `api/auth.api.ts::AuthApi` — Current user, password change, invites, invite links, pending memberships.
- `api/clash.api.ts::ClashApi` — Clash listing, resolution, rule CRUD, versioning, DSL, rule profiles.
- `api/geometry.api.ts::GeometryApi` — Cut holes, undo cuts, overlap checks, geometry history, layer type rules.
- `api/planning.api.ts::PlanningApi` — Planning cycle CRUD, contractor submissions, actualization, compare, carry-forward.
- `api/report.api.ts::ReportApi` — Report templates, sessions, auto-save, PDF/DOCX export.
- `api/revision.api.ts::RevisionApi` — Per-type `/at-time` endpoints and `loadRevision` fan-out.
- `api/weather.api.ts::WeatherApi` — Weather timeline for the ribbon.
- `api/export.api.ts::ExportApi` — GeoJSON export, permit upload, listing, and entity creation from permits.
- `api/geometadata.api.ts::GeometadataApi` — Layer CRUD, feature CRUD, building lookups, floor plans, bundle import.
- `api/entity-support.api.ts::EntitySupportApi` — Roads, deliveries, PoIs, text labels, smart groups, alerts, bulk import.
- `types/entity.types.ts::Worker` — Token entity with position, radius, temporal bounds, building placement, plan state.
- `types/entity.types.ts::Plant` — Plant entity with working radius, arc angles, inactive footprint, schedule group.
- `types/entity.types.ts::Area` — Area entity with polygon, feature type, clashable flag, temporal bounds.
- `types/entity.types.ts::DomainEntity` — Union `Worker | Plant | Area`.
- `types/entity-kind.ts::DomainEntityKind` — Discriminator `'worker' | 'plant' | 'area'`.
- `services/data-load.service.ts::DataLoadService` — Reactive orchestrator for entity reloads: tokens, plants, areas, roads, deliveries, POIs, alerts, text labels, geometadata, and planning cycle data.

## State
`EntityStore` maintains:
- `_items` (`BehaviorSubject<T[]>`) — current collection.
- `_loading` (`BehaviorSubject<boolean>`) — spinner flag.
- `_loadedOnce` — distinguishes unfetched from empty.
- `_indexById` (`Map<string, index>`) — rebuilt on every emission for O(1) `get`.

`EntityService` maintains:
- `tokenStore`, `plantStore`, `areaStore` — per-type `EntityStore` instances.
- `_conflictEvents` (`Subject<ConflictEvent>`) — 409 broadcasts.
- `_pendingOptimistic` (`Set<string>`) — IDs with in-flight optimistic updates.
- `_optimisticSnapshots` (`Map<string, any>`) — pre-optimistic state for rollback.
- `_currentContext` (`EntityLoadContext | null`) — last load parameters.
- `_deletedTokenIds` (`Set<string>`) — tombstones to filter stale HTTP snapshots.

`DataLoadService` maintains:
- `_lastLoadedSiteId`, `_lastFetchSpecs`, `_lastIncludeShadowed` — deduplication keys for `distinctUntilChanged`.

## Internals
**O(1) index.** `EntityStore._emit` builds `new Map(items.map((item, idx) => [item.id, idx]))` before every `next`. All mutations funnel through `_emit`.

**Optimistic updates.** `EntityService.optimisticUpdateToken` snapshots the current entity into `_optimisticSnapshots`, patches the store, and adds the ID to `_pendingOptimistic`. On API success the snapshot is discarded. On 409 the snapshot is discarded and `ConflictEvent` is emitted; server state patches the store. On non-409 failure the snapshot rolls back the store.

**WebSocket suppression.** `wsBatchUpdateTokens` and `wsBatchUpdatePlants` delete IDs from the incoming update map when `_pendingOptimistic.has(id)` is true. The API response handler eventually applies the authoritative state.

**Tombstones.** `deleteToken` and `wsRemoveToken` record the ID in `_deletedTokenIds`. `loadTokens`, `mergeTokens`, and `replaceTokens` call `filterDeletedTokens` → a slower HTTP snapshot cannot reintroduce a deleted token.

**Area duality.** Areas are stored as `GeometadataFeature` on the backend. `AreaApi.mapFeatureToArea` unwraps the first polygon ring from MultiPolygon. `EntityService.createArea` wraps the simple polygon back into MultiPolygon and pushes a mirrored feature into `GeometadataService`.

**Conflict resolution.** `parse409Response` extracts `detail.current`, `detail.conflicting_fields`, and `detail.client_values`. `applyMerge` re-issues the update with merged values plus `expected_updated_at`; a second 409 retriggers the conflict pipeline. `applyMerge` skips 409 re-emit for zones because the backend does not support optimistic concurrency on features.

**DataLoadService pipeline.** `setupContextLoading` watches `combineLatest([selectedSite$, requiredFetches$, appMode$])`. A site change calls `entityService.clear()` and clears delivery, POI, alert, and text-label stores. A fetch-spec or shadow-mode change triggers `forkJoin` of areas, roads, tokens, plants, deliveries, POIs, alerts, and text labels, then atomically `replaceTokens`/`replacePlants`. `forceRefreshEntities` skips while `revisionMode.enabled`, fans out temporal-context fetches, and replaces collections.

**EntityOperationsService gate.** Every method is a `dispatchByKind` visitor literal. Extending `DomainEntityKind` forces a compile error here until the new branch is added.

## Touches
- HTTP — all domain API services use `HttpClient`.
- WebSocket — `EntityService` applies deltas via `ws*` methods; `DataLoadService` handles `fullReloadRequired$` and `contextInvalidated$`.
- RxJS — `BehaviorSubject`, `Subject`, `forkJoin`, `combineLatest`, `distinctUntilChanged`, `debounceTime`, `switchMap`.

## Gotchas
- `AreaApi.listAreas` returns `GeometadataFeature[]` mapped to `Area`. The backend uses MultiPolygon; the frontend uses a simple polygon ring. Loss of inner rings is intentional for the current domain.
- `EntityService.clear()` resets `_deletedTokenIds`, `_pendingOptimistic`, and `_optimisticSnapshots`. Clearing stores without calling `entityService.clear()` leaves stale tombstones and optimistic flags.
- `DataLoadService` resolves `PlanningCycleService` lazily through the `Injector` to avoid a circular bootstrap with `DataLoadService`.
- `forceRefreshEntities` is a no-op while `revisionMode.enabled`. Exiting revision mode explicitly triggers a refresh to catch up.
- `replaceTokens` preserves IDs in `_pendingOptimistic` so optimistic state is not overwritten by an atomic replacement.
- `WorkerApi.createToken` hard-codes `radius_m: 2.6` and `token_type: 'worker'`.
- `EntityService` uses `'zone'` as the area label in 409 handling (`parse409Response`, `storeFor`, `applyMerge`) while `DomainEntityKind` uses `'area'`. The two are not interchangeable.
- `EntityService.updateArea` lacks optimistic-update and 409-rollback logic; only tokens and plants have full optimistic concurrency handling.
