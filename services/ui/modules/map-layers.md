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
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Defines every MapLibre layer, source, and render-order rule for the SimOops map, plus utilities for safe GeoJSON updates and layer visibility toggling.

## Interface

### Layer definition modules
- `app/map/map-layer-defs.ts::getGeoJsonSources` — Returns source specs for all GeoJSON (and raster) layers.
- `app/map/map-layer-defs.ts::getLayerOrder` — Returns the full `LayerSpecification[]` stack in bottom-to-top render order.
- `app/map/map-layer-defs.ts::LAYER_DEFINITIONS` — Merged layer objects from domain split files.
- `app/map/map-layer-defs.ts::GEOMETADATA_LAYER_IDS` — IDs that reference the unified `geometadata` source (used by the Zone.js recreation workaround).
- `app/map/map-layer-defs-entity.ts::ENTITY_LAYERS` — Token, plant, crane, beacon, hidden-marker, selection-glow, compare-ghost, and diff layers.
- `app/map/map-layer-defs-geometadata.ts::GEOMETADATA_LAYERS` — Fill, outline, label, pulse, and badge layers for buildings, zones, exclusions, laydowns, and work areas.
- `app/map/map-layer-defs-road.ts::ROAD_LAYERS` — Saved road casing/fill/centerline and temporary road drawing layers.
- `app/map/map-layer-defs-ui.ts::UI_LAYERS` — Measurement, clash, vertex edit, drag feedback, delivery/POI/alert pins, and presence dots.

### Source utilities
- `app/map/map-source-utils.ts::updateGeoJsonSource` — Safe `getSource` / `setData` wrapper.
- `app/map/map-source-utils.ts::updateGeoJsonSourceWithRecreate` — Zone.js/MapLibre recreation workaround on the first empty→populated transition.
- `app/map/map-source-utils.ts::recreateGeoJsonSource` — Full remove/re-add of a source and its layers.
- `app/map/map-source-utils.ts::featureCollection` — Convenience wrapper.

### Visibility controller (plain class)
- `app/map/map-layer-visibility.ts::MapLayerVisibilityController` — Applies granular layer visibility toggles (buildings, zones, workers, cranes, roads, etc.) via `setLayoutProperty` and `setFilter`.

### Raster source helpers
- `app/map/map-raster-source.ts::buildRasterSource` — Synchronous raster source spec from `SiteMap`.
- `app/map/map-raster-source.ts::resolveRasterSource` — Async TileJSON resolution with fallback.
- `app/map/map-raster-source.ts::buildBaseStyle` — Minimal MapLibre style with raster base layer.

### Barrel
- `app/map/map-layers.ts` — Re-exports layer definitions, patterns, and SVG icon helpers.
- `services/geometadata.service.ts::GeometadataService` — Layer and feature state management, visibility toggles, layer upload/update/delete, and temporal feature loading.
