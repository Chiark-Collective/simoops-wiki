---
service: ui
summary: Single source of truth for dashboard view state with derived read-only predicates.
paths:
  - services/view-mode.service.ts
  - types/view-mode.types.ts
  - services/revision-mode.service.ts
  - services/planning-cycle.service.ts
flows:
  - flows/revision-mode-navigation.md
touches: []
external: []
last_verified_commit: dbcb7815743bb868ff2c71f48501e151fbfbb932
---

## Purpose
Introduced in G11 Phase 1. Collapses three previously independent flags — `RevisionModeService.enabled$`, `PlanningCycleService.appMode$`, and `PlanningViewModeService.isReadOnly$` — into one `BehaviorSubject<ViewState>`. Phase 3 inverts ownership so `RevisionModeService.enabled$` and `PlanningCycleService.appMode$` derive from `state$` instead of being separate writers.

## Interface
- `types/view-mode.types.ts::ViewState` — Discriminated union: `editing_plan`, `editing_actual`, `viewing_submitted`, `compare`, `revision`.
- `services/view-mode.service.ts::ViewModeService` — Root service owning `_state$`.
- `services/view-mode.service.ts::SetAppModeOptions` — `cycleId`, `target`, `layout` passed to `setAppMode`.
- `services/view-mode.service.ts::ViewModeService.guardEdit` — Returns `true` and surfaces a mode-aware info toast when the dashboard is in any read-only state.
- `services/view-mode.service.ts::ViewModeService.enterRevision` / `exitRevision` — Transition methods called by `RevisionModeService`.
- `services/view-mode.service.ts::ViewModeService.setAppMode` — No-op while revision is active; preserves pre-Phase-3 derivation precedence.
- `services/view-mode.service.ts::ViewModeService.isReadOnly$` — True in `viewing_submitted`, `compare`, and `revision`.
- `services/view-mode.service.ts::ViewModeService.shouldDropLiveEvents$` — True in any read-only mode; gates WebSocket delta application.
- `services/view-mode.service.ts::ViewModeService.shouldBypassPlanFilter$` — True in any read-only mode; tells `FilteredEntityCacheService` to skip live-cycle plan-state filtering.
- `services/view-mode.service.ts::ViewModeService.useHistoricalSnapshot$` — Revision-only; switches data sources to `/at-time` endpoints.

## State
- `services/view-mode.service.ts::ViewModeService._state$` — `BehaviorSubject<ViewState>` initialized to `{ kind: 'editing_actual', cycleId: null }`. The only mutable state in the module; all writes go through transition methods.
- Invariant: `kind === 'revision'` ⟂ any planning mode. Entering revision exits `compare` and `viewing_submitted` for free.

## Internals
- Phase 1 (`dbcb7815`): `ViewModeService` derived `ViewState` from existing services; zero behavioural change.
- Phase 2a (`dbcb7815`): 42 callsites across 8 files migrated from `RevisionModeService.guardEdit` to `ViewModeService.guardEdit`. `viewing_submitted` and `compare` now block edits at the orchestrator layer, closing a latent bug where only UI affordance blocked them.
- Phase 2b (`dbcb7815`): `shouldDropLiveEvents$` and `shouldBypassPlanFilter$` broadened from revision-only to all read-only modes. `useHistoricalSnapshot$` stays revision-only because `viewing_submitted` and `compare` have their own data sources.
- Phase 3 (`dbcb7815`): Ownership inverted. `RevisionModeService` no longer owns `_enabled$`; its `enabled$` derives from `viewMode.state$`. `PlanningCycleService` no longer owns `_appMode`; its `appMode$` derives from `viewMode.state$`. Inconsistent combined states are now unrepresentable.
- `services/view-mode.service.ts::viewStateEqual` — Structural equality for `distinctUntilChanged`, comparing discriminator fields and payload values.

## Gotchas
- `setAppMode` is a silent no-op while revision is active. Callers that need to re-apply a mode after exiting revision must trigger the transition separately (the cycle-driven default logic does this automatically).
- `shouldDropLiveEvents$` covers all read-only modes, not just revision. WebSocket routers must not special-case `viewing_submitted` or `compare`.
- `useHistoricalSnapshot$` is revision-only. Consumers that gated on `shouldBypassPlanFilter$` for data-source switching must still distinguish `revision` from other read-only modes when deciding which endpoint to call.
