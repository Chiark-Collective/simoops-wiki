---
service: ui
summary: Floor plan raster rendering, interactive positioning, and building focus coordination.
paths:
  - map/map-floor-plan.ts
  - map/map-floor-plan-positioner.ts
  - services/floor-plan-placement.service.ts
  - map/map-building-focus-coordinator.ts
  - services/building-focus.service.ts
  - utils/building-visibility-policy.ts
flows:
  - Floor plan drop-to-place: idle → floor-selection → positioning → saving
  - Building focus: select → floor cycle → paint updates → visibility filter
  - Hover: mouseover building → popup state → per-floor entity counts
touches:
  - MapLibre GL JS (raster/image sources, layers, feature-state, paint expressions, mouse events)
  - DOM (Image element for dimension loading, blob URLs, cursor styles)
external:
  - TiTiler tile proxy (`/tiles/floor-plan/{id}/tilejson.json`)
  - Geometadata API (upload, update, delete, image blob)
last_verified_commit: f9606469ce367229c5c91e03c3ba917779015030
---

## Purpose
Manages floor plan raster tile display on the map, interactive positioning of non-georeferenced floor plan images, and building focus state coordination. Drives map paint updates, floor-based visibility filtering for tokens, plants, and areas, and the placement workflow state machine.

## Interface
- `map/map-floor-plan.ts::MapFloorPlanController` — Adds/removes raster tile source+layer for a floor plan; supports revision mode via `atTime` and id suffixing for split-compare.
- `map/map-floor-plan-positioner.ts::computeImageCorners` — Computes MapLibre ImageSource coordinates from center, rotation, scale, and image dimensions.
- `map/map-floor-plan-positioner.ts::computeInitialScaleMpp` — Calculates initial metres-per-pixel to fit an image inside a building bounding box.
- `map/map-floor-plan-positioner.ts::buildInvertedMask` — Builds a world-covering polygon mask with the building exterior ring as a hole.
- `map/map-floor-plan-positioner.ts::MapFloorPlanPositioner` — Interactive overlay with drag handles for translate, scale, and rotate; manages preview image, building outline, and mask layers.
- `services/floor-plan-placement.service.ts::PlacementMode` — Union type for the placement lifecycle: `'idle' | 'floor-selection' | 'positioning' | 'saving'`.
- `services/floor-plan-placement.service.ts::PlacementState` — Full state shape for the placement workflow including file, building, level, image dimensions, and placement parameters.
- `services/floor-plan-placement.service.ts::FloorPlanPlacementService` — State machine managing drop-to-place workflow, conflict retry on upload, and readjustment of existing floor plans.
- `map/map-building-focus-coordinator.ts::BuildingFocusHost` — Interface the host component implements to supply map, features, visibility settings, and repaint hooks. Includes `revisionModeActive` flag for indoor display gating in revision mode.
- `map/map-building-focus-coordinator.ts::isFeatureFloorHidden` — Pure function checking whether a feature is hidden by floor-based opacity.
- `map/map-building-focus-coordinator.ts::MapBuildingFocusCoordinator` — Owns selected building, focused floor, and hovered building state; drives map paint updates and synchronous repaints.
- `services/building-focus.service.ts::BuildingFocusContext` — `{ building, floor }` context for focus subscribers.
- `services/building-focus.service.ts::BuildingPopupState` — Hover popup state with building, position, and floor entity counts.
- `services/building-focus.service.ts::BuildingFocusService` — Manages building selection, floor cycling, hover popups, elevation intervals, and floor-based visibility calculations.
- `utils/building-visibility-policy.ts::computeFloorDisplayDecision` — Shared floor and elevation visibility rules. When `revisionModeActive` is true and no floor focus is active, indoor entities surface at full opacity regardless of `indoorMode`; an active floor focus still dims off-floor entities.
- `utils/building-visibility-policy.ts::computeAreaFloorOpacity` — Area-specific projection of `computeFloorDisplayDecision` with `indoorMode: 'always'`.

## State
`MapFloorPlanController` holds `currentKey` (composite `{id}|{atTime}|{revision_hash}` for idempotency) and `currentFeatureId` (for crosshatch dimming). `currentKey === null` → no source or layer exists on the map.

`MapFloorPlanPositioner` holds `PositionerState` (center, rotation, scale, dimensions, blob URL, building polygon) and drag bookkeeping (`dragTarget`, drag-start coordinates). Active ⇔ `state !== null`.

`FloorPlanPlacementService` exposes a single `BehaviorSubject<PlacementState>`. State transitions: `idle` → `floor-selection`/`positioning` → `positioning` → `saving` → `idle`. `imageUrl` is a blob URL created from the dropped file or an authenticated blob fetched during readjust.

`MapBuildingFocusCoordinator` tracks `selectedBuildingId`, `focusedFloor`, and `hoveredBuildingId`. It subscribes to `BuildingFocusService.hoveredBuilding$` and fans out to dirty flags + change detection.

`BuildingFocusService` maintains five `BehaviorSubject`s: `_selectedBuilding`, `_focusedFloor`, `_hoveredBuilding`, `_popupPosition`, `_popupFloorCounts`. `_pinnedPopupPosition` captures hover coordinates on click.

## Internals
**Raster lifecycle.** `MapFloorPlanController::showFloorPlan` fetches tilejson from the tile proxy, rewrites tile URLs to `.webp`, adds a raster source+layer inserted before `geometadata-fill`, then dims the building crosshatch via `setFeatureState` on the `geometadata` source. `hideFloorPlan` restores opacity and removes source+layer. The composite key decouples the controller from revision-mode concepts.

**Image corner math.** `computeImageCorners` converts metre offsets to degrees using latitude-corrected scaling (`EARTH_RADIUS_M`). Half-width/height in metres are rotated by a clockwise rotation matrix, then converted to `[lng, lat]` offsets. Returns `[[TL], [TR], [BR], [BL]]` for MapLibre ImageSource coordinates.

**Mask building.** `buildInvertedMask` produces a GeoJSON Polygon with a world exterior ring (counterclockwise) and the building's exterior ring as a hole. Used by the positioner to dim everything outside the building.

**Placement workflow.** `FloorPlanPlacementService::startDrop` creates a blob URL, loads the image to read dimensions, and transitions to `floor-selection` (multiple levels) or `positioning` (single/unknown level). `selectLevel` advances to `positioning`. `save` dispatches to `uploadWithConflictRetry` for new files or `updateFloorPlanPlacement` for readjust. On 409 Conflict, the existing plan is deleted and the upload retried once. `startReadjust` fetches the floor plan image via authenticated `HttpClient` (raw `Image()` cannot send Bearer headers) and seeds the state with existing placement parameters.

**Positioner interaction.** `MapFloorPlanPositioner` adds a MapLibre ImageSource for the preview, a GeoJSON source for handles/outline/mask, and binds `mousedown` on the handles layer. Center handle translates by delta lng/lat. Corner handle scales by distance ratio from center (`distNow / distStart`). Rotation handle sits at the midpoint of the top edge extended by 1.3× and updates `rotationDeg` via `atan2(lngDelta, latDelta)`.

**Building focus paint updates.** `MapBuildingFocusCoordinator::setFocus` triggers `updateBuildingHighlight` and `updateRasterDimming`, then calls synchronous `repaintBeacons`, `repaintGeometadata`, and `repaintBuildingBadges`. `updateBuildingHighlight` sets `fill-opacity` and `line-width`/`line-color` paint properties on `geometadata-fill` and `geometadata-outline` using `case` expressions keyed by `id` and `feature-state`. `updateRasterDimming` lowers the base `raster` layer opacity when an elevated floor is focused.

**Floor visibility filtering.** Both `MapBuildingFocusCoordinator` and `BuildingFocusService` delegate floor visibility decisions to `computeFloorDisplayDecision`. The coordinator's `getFloorBasedOpacity` and `getFloorIndicator` resolve entity elevation intervals via `getElevationInterval` and pass `indoorMode`, `elevationGrace`, `forceShowAllTokens`, and `revisionModeActive`. `BuildingFocusService::countItemsPerFloor` and `setHoveredBuilding` use FK-first authority (`building_feature_id` match) before falling back to spatial containment.

**Revision mode indoor display.** `computeFloorDisplayDecision` receives `revisionModeActive` from the host. When true and no floor focus is active, every indoor entity surfaces at full opacity so the snapshot reads as "what was there at moment T". An active floor focus still dims off-floor entities the same way as live mode, preserving the user's deliberate floor choice.

## Touches
- MapLibre GL JS raster/image sources and layers, feature-state, paint expressions, layer event binding, coordinate systems.
- DOM `Image` element for dimension extraction, `URL.createObjectURL`/`revokeObjectURL` for blob lifecycle, canvas cursor styles.

## Gotchas
- `MapFloorPlanController::hideFloorPlan` returns immediately when `currentKey === null`. In split-compare, both controllers may receive hide before any plan has been shown.
- `MapFloorPlanPositioner` uses `any` casts for `setCoordinates` and `setData`.
- `FloorPlanPlacementService` creates a blob URL in `startDrop` but revokes it only in `cleanup`; an image load failure revokes eagerly to avoid leaks.
- `BuildingFocusService::countItemsPerFloor` and `setHoveredBuilding` must use FK-first authority to stay consistent with `map-source-manager.ts:updateBuildingBadges`; spatial fallback alone drifts after polygon edits.
- `MapBuildingFocusCoordinator` updates paint properties directly on the map; the host must ensure the map instance exists or the calls are no-ops.
- `computeInitialScaleMpp` returns `0.5` fallback when the building polygon is unusable.
- `BuildingFocusHost` no longer exposes `bypassFloorDimming`. Floor focus dimming applies in every mode; revision mode indoor display is handled by `BuildingVisibilityPolicy` via the `revisionModeActive` host field.
- `computeFloorDisplayDecision` treats `revisionModeActive === true` with no floor focus as "show all indoor entities at full opacity". This overrides `indoorMode` (`hover` / `select`) so historical snapshots render comprehensibly.

(End of file - total 116 lines)
