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
flows:
  - Worker map-click → building check → level selection → token create → patch building context
  - Plant map-click → position store → modal → plant create → patch extras/building
  - Area polygon draw → validate → overlap check → create (optionally in new layer)
  - Reference polygon draw → type picker → create geometadata feature
  - Road vertex draw → validate → create → local state & history
  - Point-entity placement mode → map click → entity-specific callback
  - Permit-based creation: pending context → map click → modal defaults → create → record permit
  - Datetime resolution: permit → form shift/custom → scrubber default → undefined
touches:
  - HTTP (ApiService: building lookup, CRUD for tokens, plants, areas, roads, permit recording, overlap checks, layer creation)
external:
  - ApiService
  - EntityService
  - EntityMoveService
  - ModalService
  - PlanningViewModeService
  - RevisionModeService
  - MessageService
  - TimeModeResolver
  - TimeUtilityService
  - TimezoneService
  - GeometadataService
  - RoadEditorStateService
  - RoadHistoryService
  - ScheduleOrchestrationService
  - PermitService
  - PanelStateService
  - SiteContextService
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

## State
- `services/entity-creation-orchestrator.service.ts::EntityCreationOrchestrator` holds a `BehaviorSubject<CreationState>` (`mode`, `pendingPlantPosition`, `pendingLevelSelection`). `mode` is `CreationMode` (`'idle' | DomainEntityKind | 'road' | 'reference'`).
- `EntityCreationOrchestrator.state.mode !== 'idle' ⟂ PlanningViewModeService.isReadOnly$ === true` — read-only forces cancellation via `readonlyGuardTripped()`.
- `handlers/worker.handler.ts::WorkerHandler` lazy-injects `EntityMoveService` via `Injector` to break a circular DI dependency.
- `handlers/plant.handler.ts::PlantHandler` uses `getTargetId` to route updates for inactive cranes through `inactive_for_id`.
- `handlers/area.handler.ts::AreaHandler` tracks temporary polygon vertices in its own state during drawing; the orchestrator does not duplicate them.
- `handlers/road.handler.ts::RoadHandler` relies on `RoadEditorStateService` for drawn-vertex state and `RoadHistoryService` for undo/redo stacks.
- `handlers/permit-creation.handler.ts::PermitCreationHandler` is a plain class with two-stage state: `_pendingContext` (stage 1) and `_activePermit` + `_entityType` (stage 2).
- `handlers/point-entity-placement.handler.ts::PointEntityPlacementHandler` maintains `placementMode` and `pendingContext` per entity type.
- `dashboard/entity-creation-host/entity-creation-host.component.ts::EntityCreationHostComponent` exposes creation-mode getters that delegate to the orchestrator and workflow services.

## Internals
**Creation workflow.** `EntityCreationOrchestrator` entry points mutate `_state` to a concrete mode. `handleWorkerMapClick` calls `ApiService.getBuildingAtPoint`; multi-level buildings emit `needs_level_selection` and stash the building in `pendingLevelSelection`; single-level buildings pass the level directly to `WorkerHandler.createWorker`. `handlePlantMapClick` stores the position in `pendingPlantPosition` and emits `needs_modal`. `completeLevelSelection` resumes creation for worker, plant, or area after the user picks a level. `cancelLevelSelection` clears pending state and emits a cancellation result.

**Datetime resolution.** `CreationDatetimeResolver.resolve` follows strict precedence: 1) permit range if both bounds present; 2) form-driven shift/custom (absolute-minute sliders take priority over HH:mm because they encode overnight crossings > 24h); 3) scrubber-derived `contextDefault`; 4) `undefined`. `timeMode === 'schedule'` bypasses this resolver entirely — schedule orchestration handles it.

**Building level handling.** `WorkerHandler.placeWorker`, `PlantHandler.placePlant`, and `AreaHandler.checkBuildingAtCentroid` all use `buildingCheckWithFallback` + `classifyBuildingCheck`. Multi-level → `needs_level_selection`; single-level → auto-assign level and `buildingFeatureId`; none → create/move without context. On move, leaving a building clears `building_level` and `building_feature_id` so the entity remains visible on all floors.

**Permit flow.** `PermitCreationHandler.startPermitCreation` sets stage-1 context. When the map is clicked, `consumePendingContext` transitions to stage-2 and returns the permit/entity type. `getDefaults` scans permit text for shift keywords and returns pre-fill values for the creation modal. After creation, `consumePermit` yields the permit for metadata stamping (e.g., `created_from_permit`). `validatePlacementPosition` enforces clicks inside the matched feature polygon if `matched_feature_id` exists.

**Point entity placement.** `PointEntityPlacementHandler` is instantiated per type with a `PointPlacementConfig`. `startPlacement` sets `placementMode = true` and preserves an optional context snapshot. `handlePositionSelected` exits mode and calls `onPositionSelected`. `cancelPlacement` exits mode and calls `onCancel`, allowing modals to reopen with the preserved context.

**Handler result routing.** All handlers extend `HandlerResult<T>`, a discriminated union base with `type`, `entity`, `errors`, and `message`. The host component and workflows switch on `type` (`'created' | 'updated' | 'moved' | 'needs_level_selection' | 'needs_overlap_resolution' | 'blocked' | 'error'`).

**Road undo/redo.** `RoadHandler` records before/after snapshots in `RoadHistoryService` on every update. `undo` applies the inverse API call (`delete` for create, `create` for delete, `before` payload for update) and syncs `RoadEditorStateService`. `redo` re-applies the forward operation.

**Inactive crane routing.** `PlantHandler.getTargetId(plant)` → `plant.is_inactive && plant.inactive_for_id` guarantees updates route through the source plant’s real DB ID.

## Touches
- HTTP via `ApiService` for building lookup, token/plant/area/road CRUD, overlap checks, geometadata layer creation, and permit recording.

## Gotchas
- `WorkerHandler.moveWorker` uses debounced `EntityMoveService.updateTokenPosition` for simple moves (no building transition), but persists immediately via `EntityService.updateToken` when entering/leaving a building.
- `PlantHandler.executePlantMove` performs optimistic local updates and must keep inactive-crane siblings in sync: moving an active crane translates the inactive sibling’s `inactive_footprint_wgs84`; moving an inactive crane translates its own footprint.
- `AreaHandler.checkOverlaps` can return `blocked` (forbidden overlaps) or `needs_overlap_resolution` (exclusive overlaps). The caller must handle both before calling `createArea`.
- `AreaHandler.moveArea` does **not** persist the polygon when a multi-level building is detected; it returns `needs_level_selection` carrying the polygon so `completeMoveAreaWithLevel` can PATCH atomically.
- `RoadHandler.undo`/`redo` re-issue full API create/delete/update calls; they do not rely on local state alone.
- `CreationDatetimeResolver` ignores form values when `timeMode` is `'all-day'` or `'schedule'`. `'schedule'` is handled externally by `ScheduleOrchestrationService`.
- The orchestrator exits creation mode immediately on map click (`mode: 'idle'`) to prevent double-clicks, but the actual creation is asynchronous.
