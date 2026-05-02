---
service: ui
summary: Orchestrates entity creation flows for workers, plants, areas, roads, and point entities.
paths:
  - src/app/services/entity-creation-orchestrator.service.ts
  - src/app/services/creation-datetime-resolver.ts
  - src/app/handlers/worker.handler.ts
  - src/app/handlers/plant.handler.ts
  - src/app/handlers/area.handler.ts
  - src/app/handlers/road.handler.ts
  - src/app/handlers/permit-creation.handler.ts
  - src/app/handlers/point-entity-placement.handler.ts
  - src/app/handlers/handler-result.ts
  - src/app/dashboard/entity-creation-host/entity-creation-host.component.ts
  - src/app/dashboard/entity-creation-host/entity-creation-host.types.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Coordinates the map-click-to-entity lifecycle across all creatable types. The orchestrator manages creation mode state, building-aware level selection, and delegates to per-type handlers that perform validation, API calls, and local state updates. The creation host component wires workflows together and emits results to the dashboard.

## Interface
- `services/entity-creation-orchestrator.service.ts::EntityCreationOrchestrator` — Entry points for worker, plant, area, road, and reference creation modes; handles map clicks, building checks, and level-selection deferral.
- `services/creation-datetime-resolver.ts::CreationDatetimeResolver` — Resolves `start_at`/`end_at` from permit, form, or scrubber defaults with precedence rules.
- `handlers/worker.handler.ts::WorkerHandler` — Worker creation, movement, editing, radius scaling, and deletion with building context.
- `handlers/plant.handler.ts::PlantHandler` — Plant creation, movement, arc/radius updates, editing, and deletion with inactive-crane handling.
- `handlers/area.handler.ts::AreaHandler` — Area creation with polygon validation, overlap checks, building level handling, movement, editing, and deletion.
- `handlers/road.handler.ts::RoadHandler` — Road creation, update, deletion, undo/redo, and geometry utilities.
- `handlers/permit-creation.handler.ts::PermitCreationHandler` — Two-stage permit-to-entity flow: pending context before map click, active permit during modal.
- `handlers/point-entity-placement.handler.ts::PointEntityPlacementHandler` — Generic placement handler for deliveries, PoIs, and text labels.
- `handlers/handler-result.ts::HandlerResult` — Base discriminated union for all handler results.
- `dashboard/entity-creation-host/entity-creation-host.component.ts::EntityCreationHostComponent` — Component that hosts workflows, emits `entityCreated`, `entitySelected`, and `reloadRequested` events.
- `dashboard/entity-creation-host/entity-creation-host.types.ts::EntityCreationWorkflowBindings` — Host-facing callback interface for workflow services.
