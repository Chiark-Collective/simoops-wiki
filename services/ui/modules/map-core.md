---
service: ui
summary: MapLibre host, event wiring, source management, and subscription orchestration.
paths:
  - src/app/map/README.md
  - src/app/map/map.component.ts
  - src/app/map/map.component.html
  - src/app/map/map-event-wiring.ts
  - src/app/map/map-source-manager.ts
  - src/app/map/map-subscription-orchestrator.ts
  - src/app/map/map-bounds.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Hosts the MapLibre GL map, wires pointer/keyboard interactions, manages GeoJSON sources, and coordinates reactive subscriptions for the SimOops dashboard map.

## Interface

### Angular component
- `app/map/map.component.ts::MapComponent` — `@Component` selector `app-map`; initialises map, orchestrates controllers, and exposes `@Output() mapReady`.

### Plain classes (owned by MapComponent, not DI services)
- `app/map/map-event-wiring.ts::MapEventWiring` — Binds all MapLibre event listeners (click, hover, drag, tooltip, context menu) via the `MapEventWiringHost` interface.
- `app/map/map-source-manager.ts::MapSourceManager` — Per-domain GeoJSON source updates: beacons, plants, areas, roads, deliveries, hidden entities, crane drop zones, and clash visualisation.
- `app/map/map-subscription-orchestrator.ts::MapSubscriptionOrchestrator` — Centralises RxJS subscriptions for selection, display config, entity data, label styles, creation mode, vertex ops, presence viewports, and alerts.
- `app/map/map-bounds.ts::computeOverrideEntityBounds` — Pure helper that builds `LngLatBounds` from override-entity collections.
- `app/map/map-bounds.ts::computeOverrideEntityCacheKey` — Stable cache key for the auto-fit retry loop.

### Services consumed by MapComponent
- `app/services/map-interaction.service.ts::MapInteractionService` — `@Injectable` event bus replacing `@Output` bindings.
- `app/services/map-event-dispatch.service.ts::MapEventDispatchService` — `@Injectable` dispatcher that routes interaction events to injected services.
