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
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Visual overlays and effects on the SimOops map: grid lines, distance measurement, selection pulse, pending-entity fade, beacon generation, HTML tooltips, scene bounds, custom cursors, clash severity colours, fill patterns, alert flashing, dirty-flag batching, remote drag syncing, and dynamic icon generation.

## Interface

### Overlays & measurement (plain classes)
- `app/map/map-grid.ts::MapGridController` — Toggleable metric grid overlay via `geogrid-maplibre-gl`.
- `app/map/map-measurement.ts::MapMeasurementController` — Renders measurement points, tick marks, and a circle-based "pseudo-line" (Zone.js workaround).
- `app/map/map-measurement.ts::haversineDistance` — Distance calculation helper.

### Animations (plain classes)
- `app/map/map-pulse-animation.ts::MapPulseAnimation` — Selection ring colour interpolation (contractor → white) running outside Angular zone.
- `app/map/map-pending-pulse.ts::MapPendingPulse` — Opacity pulse (0.5–1.0) for pending tokens/plants/areas/deliveries during Review Submitted.
- `app/map/map-alert-animation.ts::MapAlertAnimation` — Opacity and size pulsing for alert pins.

### Beacon & tooltip generation (pure functions / plain class)
- `app/map/map-beacon-builder.ts::buildBeaconFeatures` — Pure function converting tokens, plants, and areas into GeoJSON features for the unified `beacons` source.
- `app/map/map-tooltips.ts::formatTokenTooltip` — HTML tooltip for workers.
- `app/map/map-tooltips.ts::formatPlantTooltip` — HTML tooltip for plants.
- `app/map/map-tooltips.ts::formatAreaTooltip` — HTML tooltip for areas.
- `app/map/map-tooltips.ts::formatDeliveryTooltip` — HTML tooltip for deliveries.

### Scene overlay & cursors (plain classes / constants)
- `app/map/map-scene-overlay.ts::MapSceneOverlay` — Scene bounds visualization for PDF export; supports box-drag custom scene drawing.
- `app/map/map-cursors.ts::WORKER_CURSOR` — SVG data-URI cursor for worker placement mode.
- `app/map/map-cursors.ts::PLANT_CURSOR` — SVG data-URI cursor for plant placement mode.
- `app/map/map-cursors.ts::AREA_CURSOR` — SVG data-URI cursor for area creation mode.
- `app/map/map-cursors.ts::ROAD_CURSOR` — SVG data-URI cursor for road creation mode.
- `app/map/map-cursors.ts::POI_CURSOR` — SVG data-URI cursor for POI placement mode.
- `app/map/map-cursors.ts::ALERT_CURSOR` — SVG data-URI cursor for alert placement mode.
- `app/map/map-cursors.ts::TEXT_LABEL_CURSOR` — SVG data-URI cursor for text-label placement mode.

### Severity, patterns, and icons (pure functions / plain class)
- `app/map/map-severity-cache.ts::buildEntitySeverityMap` — Maps entity IDs to worst clash severity.
- `app/map/map-severity-cache.ts::getEntitySeverity` — Looks up severity for a single entity.
- `app/map/map-patterns.ts::registerAreaPatterns` — Async SVG-to-pattern registration for area fill icons.
- `app/map/map-patterns.ts::createDropzoneCrosshatchPattern` — Canvas pattern for crane drop zones.
- `app/map/map-patterns.ts::createDropzoneCrosshatchPatternPump` — Canvas pattern for concrete pump drop zones.
- `app/map/map-patterns.ts::createBuildingCrosshatchPattern` — Canvas pattern for building fills.
- `app/map/map-svg-icons.ts::SvgIconManager` — Manages zoom-adaptive SVG icon rasterization.
- `app/map/map-svg-icons.ts::createResizeArrowIcon` — SDF diamond arrow for resize/radius handles.
- `app/map/map-svg-icons.ts::createAreaIcon` — Hidden-area marker icon.
- `app/map/map-svg-icons.ts::createRoadIcon` — Hidden-road marker icon.
- `app/map/map-svg-icons.ts::generatePoiPinIcons` — Per-type POI pin generation.
- `app/map/map-svg-icons.ts::generateAlertPinIcon` — Alert triangle pin generation.
- `app/map/map-svg-icons.ts::ensureDeliveryPinIcon` — Per-contractor-colour delivery pin generation.
- `app/map/map-svg-icons.ts::ensureBuildingBadgeImage` — Cached canvas badge for upper-floor entity counts.

### Scheduling & sync (plain classes)
- `app/map/map-dirty-flag-scheduler.ts::MapDirtyFlagScheduler` — Batches expensive source updates into a single `requestAnimationFrame` flush.
- `app/map/map-dirty-flag-scheduler.ts::MapDirtyFlags` — Flag bag controlling which sources need repaint.
- `app/map/map-ephemeral-position-throttler.ts::EphemeralPositionThrottler` — Inbound/outbound throttling for live remote drag visibility over WebSocket.
