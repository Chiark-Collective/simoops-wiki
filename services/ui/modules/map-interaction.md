---
service: ui
summary: Drag handlers, vertex editing, context menus, selection tools, touch adapter, pan controls, and interaction services.
paths:
  - src/app/map/map-drag.ts
  - src/app/map/map-drag-worker.ts
  - src/app/map/map-drag-plant.ts
  - src/app/map/map-drag-area.ts
  - src/app/map/map-drag-road.ts
  - src/app/map/map-drag-types.ts
  - src/app/map/map-vertex-edit.ts
  - src/app/map/map-context-menu.ts
  - src/app/map/map-context-menu.component.ts
  - src/app/map/map-selection-tools.ts
  - src/app/map/map-touch-adapter.ts
  - src/app/map/map-pan.ts
  - src/app/services/map-event-dispatch.service.ts
  - src/app/services/map-interaction.service.ts
  - src/app/services/map-interaction.types.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Handles all user interactions on the map: entity dragging, vertex editing, context menus, multi-selection tools, touch gestures, middle-mouse panning, and the typed event system that carries actions back to the dashboard.

## Interface

### Drag system (plain classes)
- `app/map/map-drag.ts::MapDragController` — Coordinates drag state across entity types; exposes `startTokenDrag`, `startPlantDrag`, `startAreaDrag`, `startRoadDrag`, and touch-drag forwarding.
- `app/map/map-drag-worker.ts::WorkerDragHandler` — Token move and radius-resize drag with clash preview.
- `app/map/map-drag-plant.ts::PlantDragHandler` — Plant move, arc-handle rotation, and radius-handle resize.
- `app/map/map-drag-area.ts::AreaDragHandler` — Area polygon translation and temp-vertex drag during creation.
- `app/map/map-drag-road.ts::RoadDragHandler` — Whole-road translation.
- `app/map/map-drag-types.ts::DragContext` — Shared map/callback/time context for all drag sub-handlers.
- `app/map/map-drag-types.ts::DragCallbacks` — Host interface consumed by drag handlers.

### Vertex editing (plain class)
- `app/map/map-vertex-edit.ts::MapVertexEditController` — Polygon vertex editing: click selection, box/lasso multi-select, edge insertion, and OT op broadcast.

### Context menus
- `app/map/map-context-menu.ts::MapContextMenuController` — Hit detection, disambiguation routing, right-click drag FSM, and menu event emission.
- `app/map/map-context-menu.component.ts::MapContextMenuComponent` — Standalone `@Component` (signals-based) that renders the context-menu UI.

### Selection tools (plain class)
- `app/map/map-selection-tools.ts::MapSelectionToolsController` — Box and lasso selection with Turf.js polygon intersection; emits selected entities via `SelectionService`.

### Touch & pan (plain classes)
- `app/map/map-touch-adapter.ts::MapTouchAdapter` — Canvas-level touch handlers for long-press context menu and entity drag on mobile.
- `app/map/map-pan.ts::MapMiddlePanController` — Middle-mouse panning (frees left-click for selection).

### Angular services
- `app/services/map-interaction.service.ts::MapInteractionService` — `@Injectable` central event bus using a typed `Subject<MapInteractionEvent>`.
- `app/services/map-interaction.types.ts::MapInteractionEvent` — Discriminated union covering all 59+ event types (worker/plant/area/road/delivery/POI/alert/layer/vertex/map events).
- `app/services/map-event-dispatch.service.ts::MapEventDispatchService` — `@Injectable` subscriber that dispatches `MapInteractionEvent`s to injected orchestrator services and component callbacks.
