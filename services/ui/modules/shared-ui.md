---
service: ui
summary: Reusable components, pipes, utilities, and constants used across the app.
paths:
  - components/collapsible-section/collapsible-section.component.ts
  - components/scrollable-time-bar/scrollable-time-bar.component.ts
  - components/weather-ribbon/weather-ribbon.component.ts
  - components/settings-modal/settings-modal.component.ts
  - pipes/floor-dots.pipe.ts
  - pipes/distance-format.pipe.ts
  - utils/api-error.ts
  - utils/logger.ts
  - utils/date-format.ts
  - constants/index.ts
  - components/index.ts
flows:
  - ScrollableTimeBar drag → viewPan / timeClick emit
  - ScrollableTimeBar wheel → scrubberMove or zoom emit
  - SettingsModal Enter → save (guarded by sub-modal/input focus)
  - SettingsModal Escape → dismiss sub-modal, then cancel
  - WeatherRibbon mousemove → tooltip display + scrubberHover emit
touches:
  - CanvasRenderingContext2D
  - ResizeObserver
  - document mouse/touch events
  - document.body tooltip append
  - setInterval
  - console
  - requestAnimationFrame
external:
  - console
  - ResizeObserver
  - CanvasRenderingContext2D
  - requestAnimationFrame
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Provides cross-cutting UI primitives, formatting pipes, error handling utilities, structured logging, and geometric/time constants so domain features do not reimplement shared concerns.

## Interface
- `components/collapsible-section/collapsible-section.component.ts::CollapsibleSectionComponent` — Standalone presentational component for a collapsible panel section with projected content, optional badge count, and configurable badge color.
- `components/scrollable-time-bar/scrollable-time-bar.component.ts::ScrollableTimeBarComponent` — Standalone interactive time bar supporting panning (click-drag / touch), shift+wheel pan, plain wheel zoom, day boundaries, shift bands, hour markers, and an optional scrubber indicator. Re-exports `scrollable-time-bar.types`.
- `components/weather-ribbon/weather-ribbon.component.ts::WeatherRibbonComponent` — Standalone canvas-based weather visualization with `ResizeObserver`, rAF-render loop, hover tooltips, and empty-state handling. Consumes `WeatherTimeline` and `ViewWindowState` inputs.
- `components/settings-modal/settings-modal.component.ts::SettingsModalComponent` — Standalone settings modal shell with tab navigation (Site, Shifts, Contractors, Invites, Clash Rules, Layer Rules, Display, Audit Log, Account). Delegates to sub-tab components via `ViewChild` and filters tabs by role.
- `pipes/floor-dots.pipe.ts::FloorDotsPipe` — Pure standalone pipe converting a worker count to up to 8 visual dots (`●`) plus a `+` indicator.
- `pipes/distance-format.pipe.ts::DistanceFormatPipe` — Pure standalone pipe formatting meters to a human-readable string (`123m`, `1.23km`).
- `utils/api-error.ts::ApiError` — Unified error class with `status`, `message`, `errors`, `body`, and `source`. Static factory `ApiError.from()` transforms `HttpErrorResponse` shapes. Exports `extractApiErrorMessage`, `isAuthError`, and `transformApiError` operator.
- `utils/logger.ts::createLogger` — Factory returning a `Logger` with `debug/info/warn/error` methods that prefix messages with a tag and route through `console.*` for capture by `ConsoleLogService`.
- `utils/date-format.ts::toLocalDateStr` — Local-timezone-safe `YYYY-MM-DD` formatter avoiding `toISOString` UTC shifts. Also exports `getRelativeTime`, `datesInRange`, and weekday constants.
- `constants/index.ts` — Barrel re-exporting `time.ts` and `geometry.ts`. Key exports include `MINUTES_PER_DAY`, `EARTH_RADIUS_M`, `DEG_TO_RAD`, `LAT_LON_METERS_PER_DEGREE`.
- `components/index.ts` — Barrel re-exporting ~70 modal, list, banner, and selection components (entity creation/edit modals, conflict banners, revision picker, rule editor, etc.).

## State
- `ScrollableTimeBarComponent` holds `computedView`, drag state (`isDragging`, `isPanning`, `dragStartX`, `dragStartViewCenter`, `dragStartMinutes`), `realTimeMinutes`, and a 60-second `setInterval` ticker. Bound document-level `mousemove`/`mouseup`/`touchmove`/`touchend` handlers are stored for teardown.
- `WeatherRibbonComponent` holds a `WeatherRibbonRenderer` instance, `ResizeObserver`, `requestAnimationFrame` id, `prepared` screen-space data, `renderScheduled` debounce flag, and a `tooltipEl` appended to `document.body`.
- `SettingsModalComponent` holds `activeTab`, `siteVisibility`, `elevationGrace`, `planningEnabled`, and `coordinatorCanSubmitPlans`. Sub-tab components are accessed via `@ViewChild`.

## Internals
- `CollapsibleSectionComponent` — `OnPush`. Projects content via `<ng-content>`. Toggle button carries `[attr.data-test-id]="'section-toggle-' + title.toLowerCase()"`. Toggle emits `void` through `EventEmitter`.
- `ScrollableTimeBarComponent` — Mouse drag threshold is 5 px; touch is 20 px. Shift+wheel pans by 60 min; plain wheel zooms 20 % per step clamped to `240`–`2880` min. `computedView` recalculated via `computeViewWindow` on `viewState` or `selectedDate` changes. Real-time indicator updates every 60 s via `setInterval` and calls `cdr.markForCheck`. Overnight shifts render by extending the day loop start by `-1` when `endMinutes < startMinutes`. `hourMarkers`, `hourLabels`, `dayNightSegments`, and `shiftBands` are getters that regenerate arrays each change-detection cycle. `hasContentLeft` / `hasContentRight` derive edge-shadow visibility from whether the view exceeds the 0–1440 minute "normal" range.
- `WeatherRibbonComponent` — DPR-aware canvas sizing via `ResizeObserver`. Render debounced to `requestAnimationFrame`; one frame per input burst. `prepareData` transforms `WeatherTimelinePoint[]` into screen-space layers using `isoToAbsoluteMinutes`. Renderer multi-passes: condition icons → precip bars → temp labels → wind arrows → time axis → forecast dimming overlay → now line → forecast-gap hatching. Wind arrows rotate by `mapBearingDeg` for geographic correctness under map rotation. Hit-testing binary-searches `sourceScreenXs`. Tooltip is a `fixed`-position `div` injected into `document.body` to escape ancestor overflow. Empty-state message is context-sensitive (`loading` / `error` / `loaded`).
- `SettingsModalComponent` — Tabs filtered by `userService.isCoordinatorOrAbove()`. Invites tab label shows `pendingMembers.length`. Lazy loads on tab selection: `layer-rules` emits `loadLayerRules`, `clash-rules` calls `clashRulesTab.loadProfiles()`, `audit-log` calls `auditLogTab.loadAuditLog()`. `@HostListener('document:keydown.enter')` and `escape` are global but short-circuit when `visible` is false. Enter suppressed when focus is in `input`/`textarea`/`select` or a sub-modal is open. Escape dismisses clash-rules sub-modal first, then closes the shell. `syncSiteVisibility` is called when `visible` becomes true, `selectedSiteId` changes, or `sites` updates, deriving `siteVisibility`, `elevationGrace`, and planning toggles from the matched site. `onSave` calls `displayTab.commitPendingSettings()` before emitting; `onCancel` calls `displayTab.discardPendingSettings()`.
- `FloorDotsPipe` — Pure. `count === 0` → `''`; `count ≤ 8` → `●` repeated; else `●`×8 + `+`.
- `DistanceFormatPipe` — Pure. Delegates to `utils/geometry.ts::formatDistance`. Null/undefined → `'0m'`.
- `ApiError` — `ApiError.from()` returns input unchanged if already an `ApiError`; otherwise extracts `status`, `message`, `errors`, and `body` from `HttpErrorResponse`-shaped objects. `extractApiErrorMessage` handles four shapes: standard FastAPI `{error:{detail:string}}`, Pydantic validation arrays `{error:{detail:[{msg}]}}`, double-nested conflicts `{error:{error:{detail}}}}`, and fallback. `isAuthError` checks `status === 401` or nested `status_code === 401`. `transformApiError` is an RxJS `catchError` + `throwError` operator. The `error` getter is a backward-compat alias for `body`.
- `createLogger` — Factory returning `Logger` with `debug/info/warn/error`. All severities route through `console.*` so `ConsoleLogService` captures output. Messages prefixed with `[tag]`.
- `toLocalDateStr` — Builds `YYYY-MM-DD` from local `getFullYear/getMonth/getDate` to avoid `toISOString` UTC date shifts. `getRelativeTime` returns `"just now"`, `"5m ago"`, etc. `datesInRange` iterates inclusive from `startDate` to `endDate`, filtering by JS day-index `Set` (defaults to `WEEKDAYS` Mon–Fri).

## Touches
- `CanvasRenderingContext2D` — `weather-ribbon-renderer.ts` draws all visualization layers.
- `ResizeObserver` — `WeatherRibbonComponent` watches container size to resize canvas and schedule re-render.
- `document` events — `ScrollableTimeBarComponent` attaches `mousemove`/`mouseup`/`touchmove`/`touchend` to `document` during drag for panning.
- `document.body` — `WeatherRibbonComponent` injects its tooltip element to escape CSS containment.
- `setInterval` — `ScrollableTimeBarComponent` 60-second real-time ticker.
- `console` — `createLogger` routes all output through `console.log`, `console.warn`, and `console.error`.

## Gotchas
- `scrollable-time-bar.component.ts::getShiftColorClass` maps `'purple'` → `'bg-orange-500'` instead of a purple Tailwind class — likely a copy-paste oversight.
- `ScrollableTimeBarComponent` getters (`hourMarkers`, `shiftBands`, `dayNightSegments`) regenerate fresh arrays on every change-detection pass despite `OnPush`. Large shift counts or rapid panning allocate frequently.
- `ScrollableTimeBarComponent` calls `event.preventDefault()` on `touchstart` and `touchmove` with `{ passive: false }`, blocking vertical page scrolling when the user initiates a touch on the bar.
- `WeatherRibbonComponent` appends its tooltip to `document.body`. Component destruction without `ngOnDestroy` running (e.g., hard navigation) leaks the tooltip DOM node.
- `SettingsModalComponent` `@HostListener('document:keydown.enter')` and `escape` fire on every keystroke globally; they guard with `if (!this.visible) return`, but the handler is still invoked.
- `SettingsModalComponent` `tabs` getter recomputes on every change-detection cycle and calls `userService.isCoordinatorOrAbove()`.
- Pure pipes (`floorDots`, `distanceFormat`) only re-evaluate on input reference change. Mutating an object property without an immutable update does not trigger re-evaluation.
- `ApiError::extractApiErrorMessage` deliberately does not fall back to `err.message`; an unrecognised shape always yields the provided fallback string.
- `toLocalDateStr` with an invalid `Date` yields `"NaN-NaN-NaN"`.
- `datesInRange` constructs `Date` objects with `new Date(startDate + 'T00:00:00')`; non-ISO-like strings produce browser-dependent parsing.
