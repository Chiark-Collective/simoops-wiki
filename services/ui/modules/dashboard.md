---
service: ui
summary: Main dashboard composition root, layout system, panels, modals, and wiring services.
paths:
  - dashboard/dashboard.component.ts
  - dashboard/layout/dashboard-layout.component.ts
  - dashboard/toolbar/toolbar.component.ts
  - dashboard/dock-bar/dock-bar.component.ts
  - dashboard/modal-host/modal-host.component.ts
  - dashboard/panel-overlay/panel-overlay.component.ts
  - services/dashboard-bootstrap-wiring.service.ts
  - services/dashboard-interaction-wiring.service.ts
  - services/panel-state.service.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
The dashboard is the single-page application root after authentication and site selection. It composes the map, entity browser, timeline, toolbar, dock bar, sliding panels, modal host, and a host of domain-specific panels into one unified construction-site management view. Wiring services separate bootstrap-time subscriptions from interaction-state side effects so the component class stays manageable.

## Interface
- `dashboard/dashboard.component.ts::DashboardComponent` — Composition root hosting the map, sidebar, timeline, modals, and entity management UI. Injects ~50 services and delegates subscription wiring to `DashboardBootstrapWiringService` and `DashboardInteractionWiringService`.
- `dashboard/layout/dashboard-layout.component.ts::DashboardLayoutComponent` — Presentational flex wrapper that projects `layout-toolbar`, `layout-dock`, and `layout-content` based on `dockPosition` (`left` | `bottom` | `top`).
- `dashboard/toolbar/toolbar.component.ts::ToolbarComponent` — Presentational top bar with app-mode dropdown, map selector, entity count badges, presence avatars, connection/offline indicators, and action outputs (search, settings, logout, reconnect, etc.). Includes responsive count-badge overflow collapse via `ResizeObserver`.
- `dashboard/dock-bar/dock-bar.component.ts::DockBarComponent` — Presentational thin strip for navigation buttons, positioned via `dockPosition` and `side`. Supports vertical and horizontal layouts.
- `dashboard/modal-host/modal-host.component.ts::ModalHostComponent` — Host for all smart modals driven by `ModalService`. Imports ~25 modal sub-components and delegates `@Output` events to `ModalResultService` so the dashboard stays decoupled from modal internals.
- `dashboard/panel-overlay/panel-overlay.component.ts::PanelOverlayComponent` — Reusable container for full-height overlay panels. On desktop: absolute left-side panel with animated width. On mobile: fixed bottom sheet with animated max-height and drag handle.
- `services/dashboard-bootstrap-wiring.service.ts::DashboardBootstrapWiringService` — Injectable that wires one-shot bootstrap subscriptions: undo result routing, site-change side effects (presence reset, layer defaults loading), and weather initialization. Called from `DashboardComponent.ngOnInit`.
- `services/dashboard-interaction-wiring.service.ts::DashboardInteractionWiringService` — Injectable that wires interaction-state subscriptions (selection, building focus, panel auto-open, creation results, schedule orchestration, clash updates, etc.) and registers dashboard callback hosts with `EntityModalOrchestrator`, `EntityInteractionOrchestrator`, `ModalResultDispatchService`, and `MapEventDispatchService`.
- `services/panel-state.service.ts::PanelStateService` — Injectable root service managing reactive `UIState` (sidebar, left overlays, right sidebar, report/imports/export panels, timeline dock, layer visibility, dock sections). Enforces mutual exclusivity between panels, auto-opens properties on selection, and persists layout preferences to `localStorage`.
