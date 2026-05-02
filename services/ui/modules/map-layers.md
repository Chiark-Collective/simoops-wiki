---
service: ui
summary: Declarative layer definitions, source utilities, visibility toggles, and raster imagery.
paths:
  - src/app/map/map-layer-defs.ts
  - src/app/map/map-layer-defs-entity.ts
  - src/app/map/map-layer-defs-geometadata.ts
  - src/app/map/map-layer-defs-road.ts
  - src/app/map/map-layer-defs-ui.ts
  - src/app/map/map-source-utils.ts
  - src/app/map/map-layer-visibility.ts
  - src/app/map/map-raster-source.ts
  - src/app/map/map-layers.ts
  - src/app/services/geometadata.service.ts
flows:
  - GeometadataService::loadLayers → map-source-utils::updateGeoJsonSourceWithRecreate → MapLibre source update
  - MapLayerVisibilityController::applyLayerVisibility → setLayoutProperty / setFilter
touches:
  - maplibre-gl
  - HTMLCanvasElement
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Defines every MapLibre layer, source, and render-order rule for the SimOops map, plus utilities for safe GeoJSON updates, layer visibility toggling, and raster base imagery.

## Interface

### Layer definition modules
- `map/map-layer-defs.ts::getGeoJsonSources` — Returns source specs for all GeoJSON (and raster) layers.
- `map/map-layer-defs.ts::getLayerOrder` — Returns the full `LayerSpecification[]` stack in bottom-to-top render order.
- `map/map-layer-defs.ts::LAYER_DEFINITIONS` — Merged layer objects from domain split files.
- `map/map-layer-defs.ts::GEOMETADATA_LAYER_IDS` — IDs that reference the unified `geometadata` source (used by the Zone.js recreation workaround).
- `map/map-layer-defs-geometadata.ts::GEOMETADATA_LAYERS` — Fill, outline, label, pulse, and badge layers for buildings, zones, exclusions, laydowns, and work areas.
- `map/map-layer-defs-entity.ts::ENTITY_LAYERS` — Token, plant, crane, beacon, hidden-marker, selection-glow, compare-ghost, and diff layers.
- `map/map-layer-defs-road.ts::ROAD_LAYERS` — Saved road casing/fill/centerline and temporary road drawing layers.
- `map/map-layer-defs-ui.ts::UI_LAYERS` — Measurement, clash, vertex edit, drag feedback, delivery/POI/alert pins, and presence dots.

### Source utilities
- `map/map-source-utils.ts::updateGeoJsonSource` — Safe `getSource` / `setData` wrapper.
- `map/map-source-utils.ts::updateGeoJsonSourceWithRecreate` — Zone.js/MapLibre recreation workaround on the first empty→populated transition.
- `map/map-source-utils.ts::recreateGeoJsonSource` — Full remove/re-add of a source and its layers.
- `map/map-source-utils.ts::featureCollection` — Convenience wrapper.

### Visibility controller
- `map/map-layer-visibility.ts::MapLayerVisibilityController` — Applies granular layer visibility toggles via `setLayoutProperty` and `setFilter`.

### Raster source helpers
- `map/map-raster-source.ts::buildRasterSource` — Synchronous raster source spec from `SiteMap`.
- `map/map-raster-source.ts::resolveRasterSource` — Async TileJSON resolution with fallback.
- `map/map-raster-source.ts::buildBaseStyle` — Minimal MapLibre style with raster base layer.

### Barrel
- `map/map-layers.ts` — Re-exports layer definitions, area patterns, and SVG icon helpers.

### Geometadata service
- `services/geometadata.service.ts::GeometadataService` — Layer and feature state management, visibility toggles, layer upload/update/delete, and temporal feature loading.

## State
- `GeometadataService` maintains `_layers`, `_features`, `_visible`, `_uploading` as `BehaviorSubject`s, plus `_currentSiteId` for temporal reloading.
- `MapLayerVisibilityController` holds only a private `map` reference; all toggle state is passed as parameters.
- `map-source-utils.ts::recreatedSourcesByMap` — `WeakMap<MlMap, Set<string>>` tracking which sources have already been recreated per map instance. After the first empty→populated recreation, subsequent updates use plain `setData()`.

## Internals

### Layer definition structure
Definitions are split by domain across four files and merged into `LAYER_DEFINITIONS`. `getLayerOrder()` assembles them into a single `LayerSpecification[]` controlling bottom-to-top render precedence: geometadata polygons → pins/presence → roads → temp drawing UI → drag feedback → selection glow → compare overlay → clash regions → inactive cranes/drop zones/arc handles → worker beacons → hidden markers → labels.

### Source update patterns
- `updateGeoJsonSource` is the baseline: `getSource` → `setData`.
- `recreateGeoJsonSource` captures layer specs from `getStyle()`, removes layers in reverse order, removes the source, re-adds the source with data pre-populated, then re-adds layers in original order below a `beforeId` computed from the original stack position.
- `updateGeoJsonSourceWithRecreate` guards recreation with `recreatedSourcesByMap`: only the first empty→populated transition triggers a recreate; all later updates use `setData()`.

### Zone.js workaround
MapLibre web workers fail to index GeoJSON sources that start empty and are later populated via `setData()`. Symptoms: `queryRenderedFeatures` and `querySourceFeatures` return zero results despite `source._data` containing features. The recreation workaround forces MapLibre to process the data by removing and re-adding the source with non-empty data.

### Raster resolution
`buildRasterSource` builds a `RasterSourceSpecification` synchronously from `SiteMap.tile_url` or `SiteMap.tilejson_url`. `resolveRasterSource` fetches TileJSON asynchronously, strips origins for proxying, and falls back to the URL-based spec on failure. `buildBaseStyle` produces a minimal MapLibre style with a dark background and the raster layer.

### Visibility toggle implementation
`applyLayerVisibility` receives a `LayerVisibilityToggles` object and drives the map via:
- `setLayoutProperty('visibility', ...)` for on/off layers
- `setFilter` for per-sub-type geometadata (`feature_type`) and plant (`plant_type`) filtering
- `plant-radius-layer` is excluded from filter management because its filter is selection-based

Static labels (`geometadata-labels`) respect `showGeometadataLabels` (U key). Active area labels and entity labels respect `showEntityLabels` (J key).

### Geometadata temporal loading
`GeometadataService::loadLayers` loads layers via `ApiService`, then loads historical features at the current scrubber timestamp via `TemporalContextService::historyTimestamp$`. Features are grouped by `layer_id` in a `Map<string, GeometadataFeature[]>`. Scrubber changes auto-trigger `reloadFeaturesForCurrentState`.

## Touches
- `maplibre-gl`
- `HTMLCanvasElement`

## Gotchas
- `circle-radius-transition: {duration:0, delay:0}` is required on all physically-sized circles to prevent MapLibre's default 300ms cross-fade lag during zoom.
- The `beacons` source sets `buffer:0, tolerance:0` to skip tile buffer generation and geometry simplification for 184+ point features, eliminating multi-second zoom delays on mobile.
- Symbol + circle layers sharing a GeoJSON source that starts empty causes Zone.js tile corruption. Resize handles (`token-resize-handle-arrows`, `radius-handle-arrow`) and vertex edit vertices use symbol-only layers to avoid this.
- `geometadata-selection-pulse` controls selection visibility via `line-width` paint property with `feature-state`, not via filter, because `feature-state` is only supported in paint properties.
- Delivery pins are runtime-generated non-SDF images; applying `icon-halo-*` (SDF-only) causes them to fail to render.
- POI pins are non-SDF icons with baked-in color; `icon-color` paint properties must not be applied.
- `inactive-crane-marker` circle-radius is dynamically overridden by `metreToPixelExpr` after source recreation; any `circle-radius-transition` would cause zoom lag.
- `plant-radius-layer` filter is managed separately for selection-based display; `applyLayerVisibility` must not touch its filter.
- `map.getStyle()` returns `undefined` after `map.remove()` → `recreateGeoJsonSource` returns early to avoid throwing in rAF callbacks that race destruction.
- `data.features.length > 0 ∧ !recreated.has(sourceId) → recreateGeoJsonSource called` ⟂ `data.features.length === 0 → plain setData even if never recreated`.
