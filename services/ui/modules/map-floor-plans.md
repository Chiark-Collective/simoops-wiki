---
service: ui
summary: Floor plan raster rendering, interactive positioning, and building focus coordination.
paths:
  - map/map-floor-plan.ts
  - map/map-floor-plan-positioner.ts
  - services/floor-plan-placement.service.ts
  - map/map-building-focus-coordinator.ts
  - services/building-focus.service.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Manages floor plan raster tile display on the map, interactive positioning of non-georeferenced floor plan images, and building focus state coordination. Includes the placement workflow state machine and floor-based visibility filtering for tokens, plants, and areas.

## Interface
- `map/map-floor-plan.ts::MapFloorPlanController` — Adds/removes raster tile source+layer for a floor plan; supports revision mode via `atTime` and id suffixing for split-compare.
- `map/map-floor-plan-positioner.ts::computeImageCorners` — Computes MapLibre ImageSource coordinates from center, rotation, scale, and image dimensions.
- `map/map-floor-plan-positioner.ts::computeInitialScaleMpp` — Calculates initial metres-per-pixel to fit an image inside a building bounding box.
- `map/map-floor-plan-positioner.ts::buildInvertedMask` — Builds a world-covering polygon mask with the building exterior ring as a hole.
- `map/map-floor-plan-positioner.ts::MapFloorPlanPositioner` — Interactive overlay with drag handles for translate, scale, and rotate; manages preview image, building outline, and mask layers.
- `services/floor-plan-placement.service.ts::PlacementMode` — Union type for the placement lifecycle: `'idle' | 'floor-selection' | 'positioning' | 'saving'`.
- `services/floor-plan-placement.service.ts::PlacementState` — Full state shape for the placement workflow including file, building, level, image dimensions, and placement parameters.
- `services/floor-plan-placement.service.ts::FloorPlanPlacementService` — State machine managing drop-to-place workflow, conflict retry on upload, and readjustment of existing floor plans.
- `map/map-building-focus-coordinator.ts::BuildingFocusHost` — Interface the host component implements to supply map, features, visibility settings, and repaint hooks.
- `map/map-building-focus-coordinator.ts::isFeatureFloorHidden` — Pure function checking whether a feature is hidden by floor-based opacity.
- `map/map-building-focus-coordinator.ts::MapBuildingFocusCoordinator` — Owns selected building, focused floor, and hovered building state; drives map paint updates and synchronous repaints.
- `services/building-focus.service.ts::BuildingFocusContext` — `{ building, floor }` context for focus subscribers.
- `services/building-focus.service.ts::BuildingPopupState` — Hover popup state with building, position, and floor entity counts.
- `services/building-focus.service.ts::BuildingFocusService` — Manages building selection, floor cycling, hover popups, elevation intervals, and floor-based visibility calculations.
