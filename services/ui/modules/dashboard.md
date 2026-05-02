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
flows:
  - dashboard/dashboard.component.ts::DashboardComponent ngOnInit sets document-level CSS accent variable and delegates bootstrap wiring
  - services/dashboard-bootstrap-wiring.service.ts::DashboardBootstrapWiringService.wireOnInitSubscriptions loads sites, sets up WebSocket, wires undo results, and resets presence on site change
  - services/dashboard-interaction-wiring.service.ts::DashboardInteractionWiringService.wireConstructorSubscriptions wires selection → panel auto-open, building focus → map focus, creation/schedule results → messages and reloads
  - services/panel-state.service.ts::PanelStateService enforces mutual exclusivity between sidebar, left overlays, right sidebar, report, imports, and export panels
  - dashboard/modal-host/modal-host.component.ts::ModalHostComponent delegates ~25 modal outputs to ModalResultService
  - dashboard/dashboard.component.ts::DashboardComponent.scheduleChangeDetection coalesces multiple markForCheck calls into a single requestAnimationFrame
touches:
  - localStorage via services/panel-state.service.ts::PanelStateService (layout prefs persistence)
  - document.documentElement.style.setProperty in dashboard/dashboard.component.ts::DashboardComponent.ngOnInit (--app-mode-accent)
  - ResizeObserver in dashboard/toolbar/toolbar.component.ts::ToolbarComponent.ngAfterViewInit (count badge overflow)
  - requestAnimationFrame in dashboard/dashboard.component.ts::DashboardComponent.scheduleChangeDetection
  - window.innerHeight / window.innerWidth in services/panel-state.service.ts::PanelStateService (panel size clamping)
external:
  - WebSocket connection initiated by services/dashboard-bootstrap-wiring.service.ts::DashboardBootstrapWiringService via DataLoadService.setupWebSocket
  - localStorage API
  - DOM APIs (ResizeObserver, requestAnimationFrame, document.documentElement.style, window dimensions)
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
The dashboard is the single-page application root after authentication and site selection. It composes the map, entity browser, timeline, toolbar, dock bar, sliding panels, modal host, and domain-specific panels into one unified construction-site management view. Wiring services separate bootstrap-time subscriptions from interaction-state side effects so the component class stays manageable.

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

## State
- `services/panel-state.service.ts::PanelStateService._uiState` — `BehaviorSubject<UIState>` holding panel visibility, dock position, timeline height, lane visibility, layer visibility, and section collapse. Reads from and writes to `localStorage` under key `simoops_layout_prefs` with schema version `7`.
- `services/panel-state.service.ts::PanelStateService._panelBeforeSelection` / `_propertiesAutoOpened` — Stack-like memory for right-sidebar auto-open/restore around selection changes.
- `dashboard/dashboard.component.ts::DashboardComponent._layerCounts` / `_layerCountsDirty` — Dirty-flag cache for entity count badges, invalidated by `scheduleChangeDetection()` and recomputed lazily in the `layerCounts` getter via `pureComputeLayerCounts`.
- `dashboard/dashboard.component.ts::DashboardComponent._planPreviewMapDataCache` / `_planPreviewMapDataCacheKey` — Ref-equality keyed cache for plan-preview map data to avoid rebuilding on every entity emission while `viewing_submitted` is active.
- `dashboard/dashboard.component.ts::DashboardComponent._cachedPopupFloorCounts` — Cached `Map<number, number>` for building-popup floor entity counts, updated on building focus changes.
- `dashboard/dashboard.component.ts::DashboardComponent.cdRafId` — Active `requestAnimationFrame` handle for coalesced change detection.
- `dashboard/toolbar/toolbar.component.ts::ToolbarComponent.countsCollapsed` / `countsNaturalWidth` — Responsive overflow state for count badges, driven by `ResizeObserver`.

## Internals
- Bootstrap wiring (`services/dashboard-bootstrap-wiring.service.ts::DashboardBootstrapWiringService.wireOnInitSubscriptions`) sets up `DataLoadService.setupContextLoading`, `DataLoadService.setupWebSocket`, undo result handling (clearing selections for deleted entities), `ModalResultDispatchService.subscribe`, site-change side effects (clear undo stack, reset presence, load layer defaults), and weather initialization. All subscriptions use `takeUntilDestroyed` bound to the service's `DestroyRef`.
- Interaction wiring (`services/dashboard-interaction-wiring.service.ts::DashboardInteractionWiringService.wireConstructorSubscriptions`) merges ~16 observables into a `toSignal` (`cdTrigger`) whose `effect` calls `scheduleChangeDetection` on the dashboard host. Additional subscriptions handle: `combineLatest` of contractors/shifts/siteMap → site config init; visible tokens/plants/areas + clashes → clash update; POI changes → selection rebound; building focus → cached floor counts + map focus push; selection → auto-open properties (`panelState.autoOpenProperties`) or restore; panel state transitions → report scene overlay cleanup; active features → filtered cache update; creation results → message + selection + modal open; schedule orchestration results → reloads + selection + area cleanup.
- Panel mutual exclusivity (`services/panel-state.service.ts::PanelStateService`): `toggleSidebar`, `toggleLeftOverlay`, `toggleRightPanel`, `toggleReportPanel`, `toggleImportsPanel`, and `toggleExportPanel` each close competing panels before opening. Opening the sidebar closes left overlays, right panels, report, imports, and export. Opening a left overlay collapses the sidebar and closes right/report/import/export. Opening a right panel collapses the sidebar and closes left/report/import/export. Report, imports, and export are mutually exclusive with each other and with sidebar/left/right panels. Pre-opening sidebar collapse state is saved for report/import/export so closing restores it.
- Auto-open/restore (`services/panel-state.service.ts::PanelStateService.autoOpenProperties` / `restoreFromAutoOpen`): when a token or plant is selected, properties opens and the previous right-sidebar panel is stashed in `_panelBeforeSelection`. When selection empties, the stashed panel is restored; if properties was opened manually, it simply closes.
- Layout persistence (`services/panel-state.service.ts::PanelStateService.persistLayoutPrefs`): persists dock position, panel widths, timeline height, lane visibility, and collapsed sections. `loadLayoutPrefs` validates fields, skips stale `timelineLaneVisibility` if stored schema version < 7, and migrates `permitsPanelWidth` → `importsPanelWidth`.
- Change-detection coalescing (`dashboard/dashboard.component.ts::DashboardComponent.scheduleChangeDetection`): invalidates `_layerCountsDirty` and `_planPreviewLayerCounts`, then schedules a single `requestAnimationFrame` to call `cdr.markForCheck()`. Multiple emissions in the same frame collapse into one CD cycle.
- Plan preview caching (`dashboard/dashboard.component.ts::DashboardComponent.planPreviewMapData`): builds a cache key from `compareData`, contractor filter, view time, and visible entity arrays. Uses `_shallowArrayEqual` to compare the key array; if unchanged, returns the cached `SplitMapSideData`. This avoids iterating ~4500 compare items + ~580 features on every entity emission while in `viewing_submitted` mode.
- Toolbar overflow (`dashboard/toolbar/toolbar.component.ts::ToolbarComponent.ngAfterViewInit`): `ResizeObserver` watches toolbar root, left section, and right section. `checkCountsOverflow` compares `left.offsetWidth + right.offsetWidth + gap` against `toolbar.clientWidth`. When collapsed, it projects used width with `countsNaturalWidth` and applies a 32px hysteresis before expanding. Runs outside `NgZone` but calls `detectChanges()` synchronously to mutate DOM before paint.
- Modal delegation (`dashboard/modal-host/modal-host.component.ts::ModalHostComponent`): every modal event handler forwards to `ModalResultService.emit` with a typed constant (e.g., `WORKER_CREATION_PLACE`, `EXPORT_GEOJSON`). The dashboard never imports modal internals; `ModalResultDispatchService` routes results back to dashboard-owned handlers.

## Touches
- `localStorage` key `simoops_layout_prefs` read/written by `services/panel-state.service.ts::PanelStateService`.
- `document.documentElement.style.setProperty('--app-mode-accent', ...)` mutated in `dashboard/dashboard.component.ts::DashboardComponent.ngOnInit`.
- `ResizeObserver` attached to toolbar DOM elements in `dashboard/toolbar/toolbar.component.ts::ToolbarComponent`.
- `requestAnimationFrame` used for CD coalescing in `dashboard/dashboard.component.ts::DashboardComponent.scheduleChangeDetection`.
- `window.innerHeight` / `window.innerWidth` read for panel size clamping in `services/panel-state.service.ts::PanelStateService`.

## Gotchas
- `DashboardBootstrapWiringService` and `DashboardInteractionWiringService` are `providedIn: 'root'`. Their `DestroyRef` is app-scoped, so subscriptions wired via `takeUntilDestroyed` live for the application lifetime. In a dashboard that is never destroyed this is harmless, but if the component could be recreated the subscriptions would leak.
- `dashboard/dashboard.component.ts::DashboardComponent.planPreviewMapData` cache relies on reference equality for its inputs. If an upstream service mutates an array or object in place instead of emitting a new reference, the cache returns stale data.
- `dashboard/dashboard.component.ts::DashboardComponent.scheduleChangeDetection` intentionally does not invalidate `_planPreviewMapDataCacheKey`. A reference-stable but content-mutated input will not trigger a rebuild until some other input changes reference.
- `services/panel-state.service.ts::PanelStateService.loadLayoutPrefs` silently swallows `JSON.parse` failures and returns `{}`, causing a full fallback to `DEFAULT_UI_STATE`. Invalid individual fields are also silently dropped.
- `dashboard/toolbar/toolbar.component.ts::ToolbarComponent` runs `ResizeObserver` outside `NgZone` yet calls `detectChanges()` inside the callback. Because `detectChanges()` can mutate layout, the observer may fire a second time in the same frame; the hysteresis guard prevents oscillation.
- `dashboard/dashboard.component.ts::DashboardComponent` exposes many getters that delegate to `EntityCreationHostComponent` ViewChild. If the host is absent (e.g., behind `*ngIf`), they return safe defaults. Setters for `newPlant`, `tempAreaPoints`, and `tempRoadPoints` silently noop when the host is missing, which can mask timing bugs.
- Adding a new modal requires updating both `dashboard/modal-host/modal-host.component.ts::ModalHostComponent` imports/handlers and `services/modal-result.service.ts::ModalResultService` constants.
- `services/panel-state.service.ts::PanelStateService` mutual-exclusion methods mutate multiple flags in a single `updateUI` call. Callers relying on intermediate state between mutations will see inconsistent values.
- `dashboard/dashboard.component.ts::DashboardComponent.activeCycleDaysRemaining` is invoked from the template and therefore executes on every change-detection cycle.
