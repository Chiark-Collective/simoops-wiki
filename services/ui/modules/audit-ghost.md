---
service: ui
summary: "Audit-section hover ghost: transient historical entity preview on the map"
paths:
  - src/app/services/audit-ghost.service.ts
  - src/app/map/map-audit-ghost.ts
  - src/app/dashboard/properties-panel/properties-panel.component.ts
flows:
  - audit-ghost-hover-flow
touches:
  - MapLibre GL
  - revision.api.ts
external: []
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose
Render a transient slate-coloured "ghost" overlay of an entity at a past audit
revision, plus its clash partners, without swapping the entire map to revision
mode. Distinct from `RevisionModeService.enter()` which gates writes and swaps
`FilteredEntityCacheService` streams.

## Interface
- `services/audit-ghost.service.ts::AuditGhostService` — Injectable; `show(siteId, entry)` / `hide()` / `clearCache()`
- `services/audit-ghost.service.ts::AuditGhostService.data$` — `Observable<AuditGhostFetch | null>`; primary output consumed by `MapAuditGhostController`
- `services/audit-ghost.service.ts::AuditGhostService.active$` — `Observable<boolean>`; derived from `data$` (tests only)
- `services/audit-ghost.service.ts::AuditGhostFetch` — `{ atTime, primary, partnerWorkers, partnerPlants, partnerFeatures, clashes }`; `primary` is `AuditGhostPrimary | null`
- `services/audit-ghost.service.ts::AuditGhostPrimary` — discriminated union `{ kind: 'worker'|'plant'|'feature', data }`
- `map/map-audit-ghost.ts::MapAuditGhostController` — MapLibre overlay controller; `attach(map)` / `detach()`; `render(data)` is public for testing only

## State
- `AuditGhostService._data$` — `BehaviorSubject<AuditGhostFetch | null>`; holds current ghost data and broadcasts to subscribers
- `AuditGhostService._cache` — LRU `Map<string, AuditGhostFetch>` capped at 20 entries; keyed on `(siteId, entityType/entityId, timestamp, action)`
- `AuditGhostService._request$` — `Subject<ShowRequest | null>`; drives `switchMap` concurrency so latest hover wins
- `MapAuditGhostController.pending` — buffers the latest emission when map is not yet attached

Invariants:
- `show()` cancels in-flight previous fetch via `switchMap`
- `deleted` entries use `timestamp - 1ms` so at-time snapshot returns pre-deletion state
- Action included in cache key so `deleted` and `updated` lookups for same row don't alias

## Internals
- Hover timing: 200ms enter debounce (`PropertiesPanelComponent.HOVER_ENTER_MS`) before calling `show()`; 100ms leave grace (`PropertiesPanelComponent.HOVER_LEAVE_GRACE_MS`) before calling `hide()` — prevents flicker on accidental cursor drift
- `AuditGhostService._fetch` calls `RevisionApi` workers/plants/features/clashes at time; `involving` param filters clashes to primary entity
- `snapshotInstant` adjusts `deleted` timestamps by -1ms because `AuditSnapshotReconstructor` filters out deletion-marked snapshots at exact T
- `MapAuditGhostController.render` builds Point/Polygon/LineString GeoJSON features and writes to four `audit-ghost-*` sources
- Five layer IDs toggled together: `audit-ghost-tokens-circle`, `audit-ghost-plants-circle`, `audit-ghost-features-fill`, `audit-ghost-features-outline`, `audit-ghost-clash-lines`
- Clash line endpoints resolved from entity positions; missing endpoints skipped (e.g. inactive-crane synthetic IDs)
- Controller is re-entrant: `attach` after `detach` replays pending emission

## Touches
| resource | how | why |
|---|---|---|
| MapLibre GL | `setData` on `audit-ghost-*` sources, `setLayoutProperty('visibility')` | Render transient overlay |
| revision.api.ts | `listWorkersAtTime`, `listPlantAtTime`, `listFeaturesAtTime`, `listClashesAtTime` | Fetch historical snapshot |

## Gotchas
- Ghost is purely visual — no write gating, no `FilteredEntityCacheService` swap
- Cache capped at 20; panel sessions with heavy back-and-forth hovering may evict older entries
- `clearCache()` called on entity-selection change to prevent stale snapshots bleeding across selections
- Clash line drawing skips partners whose positions are absent (inactive cranes not in at-time payload)