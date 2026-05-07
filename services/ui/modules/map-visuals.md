---
service: ui
summary: Grid overlay, measurement tool, pulse animations, beacons, tooltips, scene overlays, cursors, severity cache, patterns, and alert animations.
paths:
  - src/app/map/map-grid.ts
  - src/app/map/map-measurement.ts
  - src/app/map/map-pulse-animation.ts
  - src/app/map/map-pending-pulse.ts
  - src/app/map/map-beacon-builder.ts
  - src/app/map/map-tooltips.ts
  - src/app/map/map-scene-overlay.ts
  - src/app/map/map-cursors.ts
  - src/app/map/map-severity-cache.ts
  - src/app/map/map-patterns.ts
  - src/app/map/map-alert-animation.ts
  - src/app/map/map-dirty-flag-scheduler.ts
  - src/app/map/map-ephemeral-position-throttler.ts
  - src/app/map/map-svg-icons.ts
  - src/app/map/map-source-utils.ts
flows: []
touches:
  - Canvas
  - MapLibre GL
  - DOM
  - requestAnimationFrame
external:
  - geogrid-maplibre-gl
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose
Visual overlays and effects on the SimOops map: metric grid, distance measurement, selection pulse, pending-entity fade, beacon generation, HTML tooltips, scene bounds, custom cursors, clash severity colours, fill patterns, alert flashing, dirty-flag batching, remote drag sync, and dynamic icon rasterization.

## Interface

### Overlays & measurement
- `app/map/map-grid.ts::MapGridController` — Toggleable metric grid via `geogrid-maplibre-gl`. Computes meter intervals from zoom level and labels offsets from the grid center.
- `app/map/map-measurement.ts::MapMeasurementController` — Renders measurement points, tick marks with distance labels, and a circle-based "pseudo-line" workaround.
- `app/map/map-measurement.ts::haversineDistance` — Haversine distance helper.
- `app/map/map-scene-overlay.ts::MapSceneOverlay` — Scene bounds for PDF export; supports box-drag custom scene drawing, click/hover interaction, and rotation-aware polygons.

### Animations
- `app/map/map-pulse-animation.ts::MapPulseAnimation` — Selection ring colour interpolation (contractor → white) running outside Angular zone. 1200 ms cycle.
- `app/map/map-pending-pulse.ts::MapPendingPulse` — Opacity pulse (0.5–1.0) for pending tokens/plants/areas/deliveries during Review Submitted. 1400 ms cycle.
- `app/map/map-alert-animation.ts::MapAlertAnimation` — Opacity (0.3–1.0) and size (0.85x–1.15x) pulsing for alert pins. 800 ms cycle.

### Beacon & tooltip generation
- `app/map/map-beacon-builder.ts::buildBeaconFeatures` — Pure function converting tokens, plants, areas, and arc handles into GeoJSON for the unified `beacons` source.
- `app/map/map-tooltips.ts::formatTokenTooltip` — HTML tooltip for workers.
- `app/map/map-tooltips.ts::formatPlantTooltip` — HTML tooltip for plants.
- `app/map/map-tooltips.ts::formatAreaTooltip` — HTML tooltip for areas.
- `app/map/map-tooltips.ts::formatDeliveryTooltip` — HTML tooltip for deliveries.

### Cursors
- `app/map/map-cursors.ts::WORKER_CURSOR` — SVG data-URI cursor for worker placement.
- `app/map/map-cursors.ts::PLANT_CURSOR` — SVG data-URI cursor for plant placement.
- `app/map/map-cursors.ts::AREA_CURSOR` — SVG data-URI cursor for area creation.
- `app/map/map-cursors.ts::ROAD_CURSOR` — SVG data-URI cursor for road creation.
- `app/map/map-cursors.ts::POI_CURSOR` — SVG data-URI cursor for POI placement.
- `app/map/map-cursors.ts::ALERT_CURSOR` — SVG data-URI cursor for alert placement.
- `app/map/map-cursors.ts::TEXT_LABEL_CURSOR` — SVG data-URI cursor for text-label placement.

### Severity, patterns, and icons
- `app/map/map-severity-cache.ts::buildEntitySeverityMap` — Maps entity IDs to worst active clash severity. Red overrides amber; resolved clashes excluded.
- `app/map/map-severity-cache.ts::getEntitySeverity` — Looks up severity for a single entity.
- `app/map/map-patterns.ts::registerAreaPatterns` — Async SVG-to-pattern registration for area fill icons.
- `app/map/map-patterns.ts::createDropzoneCrosshatchPattern` — Canvas pattern for crane drop zones.
- `app/map/map-patterns.ts::createDropzoneCrosshatchPatternPump` — Canvas pattern for concrete pump drop zones.
- `app/map/map-patterns.ts::createBuildingCrosshatchPattern` — Canvas pattern for building fills.
- `app/map/map-svg-icons.ts::SvgIconManager` — Zoom-adaptive SVG rasterization via `zoomend`; re-rasterizes when needed size exceeds current by >50% or shrinks below 25%
- `app/map/map-svg-icons.ts::createResizeArrowIcon` — SDF diamond arrow for resize/radius handles.
- `app/map/map-svg-icons.ts::createAreaIcon` — Hidden-area marker icon.
- `app/map/map-svg-icons.ts::createRoadIcon` — Hidden-road marker icon.
- `app/map/map-svg-icons.ts::generatePoiPinIcons` — Per-type POI pin generation (fire extinguisher, medic, fire assembly, smoke shelter, generic) as full-colour 128px canvas images.
- `app/map/map-svg-icons.ts::generateAlertPinIcon` — Amber triangle with exclamation mark.
- `app/map/map-svg-icons.ts::ensureDeliveryPinIcon` — Per-contractor-colour delivery teardrop pin with truck glyph; lazily generated and cached per unique hex colour.
- `app/map/map-svg-icons.ts::ensureBuildingBadgeImage` — Pre-rendered building badge with worker count + area count as cached canvas images; uses `drawHardhatGlyph` and `drawHexagonGlyph`.
- `app/map/map-svg-icons.ts::contractorLogoImageId()` / `ensureContractorLogoIcon()` / `removeContractorLogoIcon()` — Full contractor logo pipeline: loads raster/SVG, crops transparent letterbox, inscribes into circle with contractor-coloured border, registers as MapLibre image. Uses `CONTRACTOR_LOGO_INSCRIBE_FACTOR` (0.94) for sizing relative to token/plant circle.

### Source utilities
- `app/map/map-source-utils.ts::RecreatableMapSource` — Typed wrapper around a GeoJSON source + layers. Owns the empty→populated recreation workaround for the Zone.js/MapLibre bug, then replays recorded `setFilter` / `setFeatureState` / `setLayoutProperty` / `setPaintProperty` calls so dynamic state survives the recreate cycle. Caps replay log at 10,000 entries.
- `app/map/map-source-utils.ts::updateGeoJsonSource` / `recreateGeoJsonSource` / `updateGeoJsonSourceWithRecreate` — Free-function helpers for the same workaround.
- `app/map/map-source-utils.ts::mapEventSignal` — Bridges a MapLibre event into an Angular signal, unregistering on `DestroyRef` destroy. Needed because MapLibre handlers fire outside NgZone and `markForCheck` races under worker contention.

### Scheduling & sync
- `app/map/map-dirty-flag-scheduler.ts::MapDirtyFlagScheduler` — Batches expensive source updates into a single `requestAnimationFrame` flush.
- `app/map/map-dirty-flag-scheduler.ts::MapDirtyFlags` — Flag bag controlling which sources need repaint.
- `app/map/map-ephemeral-position-throttler.ts::EphemeralPositionThrottler` — Inbound/outbound throttling for live remote drag visibility over WebSocket.

## State

- `MapGridController` — `geoGrid?: GeoGrid`, `gridVisible: boolean`, `gridRefLat/Lon: number` (center at toggle time).
- `MapPulseAnimation` — `animationFrameId: number | null`, `startTime`, `lastFrameTime` (mobile frame-skip gate).
- `MapPendingPulse` — `animationFrameId`, `startTime`, `lastFrameTime`. `TARGETS` registry is immutable after load.
- `MapAlertAnimation` — `animationFrameId`, `startTime`, `lastFrameTime`, `hasAlerts: boolean`, `_baseScale`, `_opacityScale`.
- `MapSceneOverlay` — `map`, `drawingMode`, `drawStartPx`, `onDrawComplete`, `lastHoveredSceneId`, bound handler references.
- `MapDirtyFlagScheduler` — `flags: MapDirtyFlags`, `scheduled: boolean`, `rafId: number`.
- `EphemeralPositionThrottler` — `lastSendTime: Map<string, number>`, `inboundSubs: Array<{ unsubscribe }>`.
- `SvgIconManager` — `icons: Map<string, { img, baseSize, basePixelRatio, currentRasterSize, zoomAdaptive }>`, `map`, `zoomHandler`.
- `RecreatableMapSource` — `recreated: Set<string>` (shared module-level tracker), `appliedFilters: Map<string, unknown>`, `appliedFeatureStates: Map<string | number, Record<string, unknown>>`, `appliedLayoutProps: Map<string, Map<string, unknown>>`, `appliedPaintProps: Map<string, Map<string, unknown>>`.

## Internals

### Grid
`MapGridController.toggle` instantiates `GeoGrid` once, anchoring labels to the map center at toggle time. `gridDensity` converts zoom → meter interval → degrees using averaged meters-per-degree at that latitude. `formatLabels` decides whether a label axis is lat or lon by proximity to the reference point, then prints offset in `m`/`km`.

### Measurement
`MapMeasurementController.update` reads the current point list, computes total distance with `haversineDistance`, then writes three GeoJSON sources:
- `measurement-points` — vertex circles.
- `measurement-ticks` — labelled major/minor tick features placed along segments at intervals chosen by total distance.
- `measurement-line-dots` — densely spaced circles substituting for a line layer.

`updateLineDots` spaces dots every 1–5 m along segments. This is a Zone.js workaround: MapLibre line layers fail to render when created from an Angular zone context.

### Selection pulse
`MapPulseAnimation` runs a RAF loop outside Angular zone. Each frame it computes `t = 0.5 + 0.5 * sin(2π * phase)` over a 1200 ms cycle and interpolates contractor colour → `#ffffff`. For single-colour selections it sets a static paint property; for multi-selections it builds a `match` expression keyed on `contractor_color`. Token pulse targets `selection-pulse` (circle-stroke); area pulse targets `geometadata-selection-pulse` (line-color/line-opacity).

### Pending pulse
`MapPendingPulse` runs a 1400 ms RAF loop outside Angular zone, rewriting the `pending-factor` slot of each registered layer's paint expression every frame. `caseExpr(factor)` branches on `is_pending`; non-pending features stay at 1.0. Registered layers: `beacons-radius`, `plant-radius-layer`, `plant-drag-layer`, `delivery-pins`, and all `geometadata-*-fill` variants. `stop()` resets every layer to factor 1 so PNG exports/screenshots are faithful.

### Beacon builder
`buildBeaconFeatures` is a pure function. It iterates tokens (severity colour, floor opacity, search opacity, pending flag, contractor colour, label), skips inactive cranes for plants, computes area centroids with `getPolygonCentroid`, and appends arc-handle features for the selected crane/pump using `getArcHandlePosition`. All features land in the unified `beacons` GeoJSON source consumed by MapLibre symbol/circle layers.

### Tooltips
Four pure formatting functions return HTML strings. `formatTokenTooltip` and `formatDeliveryTooltip` accept an optional `PlanningCycleLookup` to resolve cycle names. Contractor colours come from `getContractorColor`. Badges use muted/dim/tag-blue constants. Delivery tooltips include a status colour map.

### Scene overlay
`MapSceneOverlay` manages a single GeoJSON source with four layers: accepted fill (0.15 opacity), rejected fill (0.06 opacity), outline (dashed), and highlighted fill (0.35 opacity). `updateScenes` prefers explicit `polygon` rings when available, falling back to axis-aligned bounds. `bindInteraction` uses `queryRenderedFeatures` on `INTERACTIVE_LAYERS` to dispatch click/hover. Box-drawing mode disables `dragPan`, sets a base64 crosshair cursor, and unprojects screen rectangle corners to geo on mouseup; only fires if the rectangle exceeds ~11 m.

### Cursors
Each cursor is a 128×128 SVG data-URI with hotspot at (64, 64). A shared crosshair (white strokes overlaid with black 1 px outlines) provides contrast on all backgrounds; the tool icon sits in the bottom-right quadrant.

### Severity cache
`buildEntitySeverityMap` walks active (non-resolved) clashes and writes the worst severity per entity ID into a `Map<string, 'amber' | 'red'>`. `getEntitySeverity` defaults to `'green'`.

### Patterns
`registerAreaPatterns` fetches SVG assets, extracts the first `<path>` `d` attribute via `DOMParser`, scales it onto a 64×64 transparent canvas tile, and registers with `pixelRatio: 2`. Crosshatch patterns are procedural: orange (`#f97316`) + black diagonals for crane drop zones, red (`#dc2626`) + black for pump drop zones, and semi-transparent blue-gray for buildings.

### SVG icons
`SvgIconManager` loads SVGs into `HTMLImageElement`s, rasterizes once at `baseSize`, and re-rasterizes on `zoomend` when the needed size exceeds current by >50% or shrinks below 25%. `pixelRatio` is adjusted so native display size stays constant. `createResizeArrowIcon` builds a 128×128 SDF diamond by computing signed distance to each edge and encoding distance into the alpha channel (192 = boundary per MapLibre SDF threshold). `generatePoiPinIcons` draws 128×128 full-colour circles with white glyphs (generic, fire extinguisher, medic, fire assembly, smoke shelter). `ensureDeliveryPinIcon` draws a contractor-coloured teardrop with a canvas truck glyph and uses `map.updateImage` if the name already exists. `ensureBuildingBadgeImage` renders a rounded pill with hardhat/hexagon glyphs and worker/area counts, cached per map in a `WeakMap<Set<string>>`.

### Dirty-flag scheduler
Callers mutate `scheduler.flags.<name> = true` and call `schedule()`. The scheduler queues one RAF; inside the callback it snapshots the flag bag, replaces it with a fresh empty object, and invokes `applyDirty(snapshot)`. This ensures updates that fire during `applyDirty` land in the next frame rather than being dropped.

### Ephemeral throttler
Inbound subscriptions mutate the host's `tokens` and `plant` arrays in place, then call `updateBeacons()` / `updatePlantSource()`. Outbound sends are gated by `lastSendTime` per entity ID with a 100 ms cooldown. Contractor ID is resolved from the local array at send time.

## Touches
- **Canvas** — pattern generation, SDF rasterization, badge rendering, icon rasterization.
- **MapLibre GL** — sources, layers, paint/layout properties, images, `queryRenderedFeatures`, `unproject`.
- **DOM** — `DOMParser` for SVG paths, `HTMLImageElement` loading, cursor data-URIs, canvas elements.
- **requestAnimationFrame** — pulse animations, dirty-flag flush.
- **WebSocket** — ephemeral position/radius/arc broadcasts and subscriptions.

## Gotchas
- Zone.js line-layer bug ⟂ `measurement-line-dots` pseudo-line workaround. Do not replace dots with a line layer without verifying Angular zone context.
- `MapPendingPulse` paint builders must stay in sync with the static layer definitions in the map setup. A mismatch silently overwrites paint with stale math.
- `MapSceneOverlay` drawing mode disables `dragPan`. Failing to call `stopDrawing` leaves pan disabled.
- `buildBeaconFeatures` severity colours are hardcoded (`#22c55e`, `#f59e0b`, `#ef4444`) — not derived from a theme. Changing clash colours requires updating both the cache and the builder.
- `ensureBuildingBadgeImage` uses a `WeakMap` keyed by map instance. Badges are never removed; memory grows with unique count combinations.
- `MapPulseAnimation` and `MapPendingPulse` both rewrite paint properties. Running simultaneously on the same layer property is undefined — currently they target different layers.
- `MapAlertAnimation` `setOpacityScale` is used to dim alerts when other toolbar badges are hovered. Setting `baseScale` while animating is safe; setting it while stopped resets the layer immediately.
- `EphemeralPositionThrottler` mutates host arrays in place to bypass `FilteredEntityCache` rebuilds. Direct mutation means change detection does not fire; beacon rebuilds must be triggered explicitly.
- `registerAreaPatterns` expects SVGs with a single `<path>` element; multi-path icons silently render only the first path.
- `RecreatableMapSource` shares its recreate tracker with `updateGeoJsonSourceWithRecreate` via a module-level `WeakMap<MLMap, Set<string>>`. Mixing class and free-function usage on the same source is safe, but calling `setData` directly on the MapLibre source bypasses the tracker and can break the replay log.
- `mapEventSignal` registers a native MapLibre handler. Callers must pass a `DestroyRef` or the handler leaks.
