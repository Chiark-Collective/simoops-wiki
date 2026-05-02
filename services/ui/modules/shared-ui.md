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
flows: []
touches: []
external: []
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
