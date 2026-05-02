---
service: ui
summary: Selection state, filtering, visibility, centering, hidden entities, and area interaction.
paths:
  - src/app/services/selection.service.ts
  - src/app/services/selection-filter.service.ts
  - src/app/services/filtered-entity-cache.service.ts
  - src/app/services/hover-state.service.ts
  - src/app/services/entity-visibility.service.ts
  - src/app/services/entity-centering.service.ts
  - src/app/services/hidden-entities.service.ts
  - src/app/services/area-feature-interaction.service.ts
  - src/app/services/area-feature-types.ts
  - src/app/services/visibility-settings.service.ts
  - src/app/services/entity-interaction-orchestrator.service.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Unified selection and visibility subsystem. `SelectionService` manages typed single-entity and `SpatialEntity` multi-selection with tool state. `FilteredEntityCacheService` combines temporal visibility, hidden entities, and plan-state filtering into stable cached arrays. `EntityVisibilityService` produces reactive filtered streams for tokens, plants, and areas. `AreaFeatureInteractionService` coordinates area selection, vertex editing, hole cutting, and layer operations.

## Interface
- `services/selection.service.ts::SelectionService` — Typed selection (worker, plant, feature, road, poi), spatial multi-selection with add/toggle modes, selection tools (box, lasso), and clear operations.
- `services/selection-filter.service.ts::SelectionFilterService` — Client-side filtering engine supporting type, contractor, planning cycle, and SmartGroup query selection.
- `services/filtered-entity-cache.service.ts::FilteredEntityCacheService` — Three-layer pipeline producing stable visible/hidden/clash entity arrays with plan-state and revision-mode awareness.
- `services/hover-state.service.ts::HoverStateService` — Hover entity and clash popup state.
- `services/entity-visibility.service.ts::EntityVisibilityService` — Reactive streams `visibleTokens$`, `visiblePlants$`, `visibleAreas$`, `activeFeatures$`, and temporal-only clash streams.
- `services/entity-centering.service.ts::EntityCenteringService` — Map camera centering on workers, plants, areas, roads, PoIs, and active features.
- `services/hidden-entities.service.ts::HiddenEntitiesService` — Session-only per-type hidden ID tracking with toggle, show, and show-all operations.
- `services/area-feature-interaction.service.ts::AreaFeatureInteractionService` — Area selection, vertex edit coordination, hole cutting, undo cuts, feature type changes, layer deletion, and building edit routing.
- `services/area-feature-types.ts::ACTIVE_AREA_FEATURE_TYPES` — Canonical set of active area feature types (`exclusion`, `laydown`, `work_area`).
- `services/visibility-settings.service.ts::VisibilitySettingsService` — Opacity, color, and misc display settings with localStorage persistence.
- `services/entity-interaction-orchestrator.service.ts::EntityInteractionOrchestrator` — Routes entity clicks on the map to selection, building/floor coordination, and panel state updates.
