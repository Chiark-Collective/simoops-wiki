---
service: ui
summary: Report session lifecycle, scene capture, template management, and export.
paths:
  - services/report-orchestrator.service.ts
  - services/report-session.service.ts
  - services/report-session-sync-binding.service.ts
  - api/report.api.ts
  - dashboard/report-panel/
  - components/report-wizard/
  - types/report.types.ts
  - map/map-scene-overlay.ts
  - utils/minimap-compositor.ts
  - utils/overview-grid-compositor.ts
  - utils/tile-grid.ts
  - utils/report-merge.ts
  - utils/report-sticky-defaults.ts
  - services/export.service.ts
flows: []
touches:
  - http
  - websocket
  - canvas
  - maplibre
  - localstorage
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Orchestrates report generation workflows: scene selection on the map, session creation/autosave, template-based report building, and PDF/DOCX export. Syncs report session state via WebSocket.

## Interface
- `services/report-orchestrator.service.ts::ReportOrchestrator` — Scene overlay management (`MapSceneOverlay`), custom bounds drawing, scene capture with minimap compositing, and export coordination.
- `services/report-session.service.ts::ReportSessionService` — Report session state (picker, form, autosave), sticky defaults, delivery integration, and export request building. Emits `saveStatus$` (`saved` | `saving` | `unsaved` | `error`).
- `services/report-session.service.ts::ReportWizardView` — `'picker'` | `'form'`.
- `services/report-session.service.ts::ReportSaveStatus` — `'saved'` | `'saving'` | `'unsaved'` | `'error'`.
- `services/report-session.service.ts::ReportExportRequest` — `{ sessionId, format, displayOptions }`.
- `services/report-session-sync-binding.service.ts::ReportSessionSyncBinding` — Bridges WebSocket report events into `ReportSessionService`.
- `api/report.api.ts::ReportApi` — HTTP wrapper for report templates, sessions, and export endpoints.
- `dashboard/report-panel/report-panel.component.ts::ReportPanelComponent` — Thin presenter for report session UI.
- `components/report-wizard/report-section-scene-selection.component.ts::ReportSectionSceneSelectionComponent` — Scene accept/reject, display options, custom overview, tile grid controls.
- `components/report-wizard/report-section-metadata.component.ts::ReportSectionMetadataComponent` — Label/input grid for metadata sections.
- `components/report-wizard/report-section-table.component.ts::ReportSectionTableComponent` — Editable table with add/remove rows.
- `components/report-wizard/report-section-dynamic-group.component.ts::ReportSectionDynamicGroupComponent` — Collapsible zone-by-zone tables.
- `types/report.types.ts` — `ReportTemplate`, `ReportSession`, `ReportScene`, `SceneDisplayOptions`, `CustomOverviewBounds`, etc.

## State
`ReportSessionService` owns all runtime state via BehaviorSubjects:
- `view$: ReportWizardView` — `'picker'` or `'form'`.
- `templates$: ReportTemplateSummary[]` — Loaded for the current site.
- `drafts$: ReportSessionSummary[]` — Draft sessions for the site.
- `completedSessions$: ReportSessionSummary[]` — Completed sessions.
- `session$: ReportSession | null` — Active session with `form_data` and `context_snapshot`.
- `template$: ReportTemplate | null` — Schema driving section rendering.
- `formData$: Record<string, unknown>` — Mutable section data; mutated by section components.
- `saveStatus$: ReportSaveStatus` — `'saved'` | `'saving'` | `'unsaved'` | `'error'`.
- `suggestions$: Record<string, string[]>` — Autocomplete lists (e.g. contractor names).
- `sessionContractors$: {id, name, color_hex}[]` — Contractors from session context.
- `refreshing$: boolean` — Live section refresh in progress.
- `exporting$: boolean` — Export pipeline running.
- `completing$: boolean` — Completion request in flight.

`ReportOrchestrator` owns map-interaction state:
- `sceneOverlay: MapSceneOverlay` — GeoJSON source + layers for scene bounds.
- `isDrawingScene$: boolean` — Custom box-drawing mode active.
- `customOverviewBounds$: CustomOverviewBounds | null` — User-drawn overview bounds.
- `mapHoveredSceneId$: string | null` — Scene ID hovered on the map.
- `reportScenes: ReportScene[]` — Cached scenes for overlay rendering.

## Internals
**Scene capture workflow.** `ReportOrchestrator::onReportExport` captures screenshots for each accepted scene:
1. Hide scene overlay layers and configure label/zone/building visibility per `SceneDisplayOptions`.
2. Capture overview image for minimap (hides clutter layers; crops to custom bounds or entity bounds).
3. For each accepted scene: restore `view_at` temporal state; if `viewState` + `polygon` exist, call `captureRotatedSnip` (restores draw-time bearing/zoom/center, projects polygon corners to canvas pixels, crops to axis-aligned bbox); else `fitBounds` + `captureMapWithCompass`.
4. If `showMinimap` is enabled, composite overview inset via `compositeMinimapIntoScene` with yellow highlight rect.
5. If tile subdivision enabled, compute `TileGridSummary`, capture up to 50 occupied tiles, and composite grid lines onto overview via `compositeGridOntoOverview`.
6. Restore map view, filters, labels, and overlay layers; pass image arrays to `doExport`.

**Autosave debounce.** `ReportSessionService::setSectionData` updates `formData$`, sets `saveStatus$` to `'unsaved'`, and pushes to `saveSubject`. A `debounceTime(2000)` pipeline filters out completed sessions, PATCHes `form_data`, then updates `saveStatus$` to `'saved'` and persists sticky defaults.

**Export coordination.** `startExport` forces a save if `saveStatus === 'unsaved'`, then emits `requestExport$` if accepted scenes exist. The dashboard's `ReportOrchestrator` handles capture and calls `ReportPanelComponent::doExport`, which delegates to `ReportSessionService::doExport` to POST the blob and trigger download.

**Live refresh.** `setupLiveRefresh` subscribes to `entityService.tokens$`, `plants$`, and `clashState.clashes$` with `skip(1)` + `debounceTime(7000)`. Calls `refreshReportContext` and merges results via `mergeZoneCoordination` and `mergeClashScenes`, preserving user edits, custom scenes, and display options.

**Sync bindings.** `ReportSessionSyncBinding` registers with `ConfigSyncService` on the `report_session` channel. Routes `created`/`updated`/`deleted` ops to `wsApplyReportSession*` methods. Updates only touch drafts/completed lists; live `session$` is updated only when `saveStatus === 'saved'` to avoid clobbering in-flight edits.

**Sticky defaults.** `applyStickyDefaults` reads `localStorage` per site and injects missing front-matter values. `persistStickyDefaults` extracts sticky keys after each successful save and writes them back.

## Touches
- `api/report.api.ts` → `ReportApi` → HTTP endpoints for templates, sessions, refresh-context, export.
- `services/config-sync.service.ts` → `ConfigSyncService` → WebSocket `report_session` channel.
- `map/map-scene-overlay.ts` → `MapSceneOverlay` → MapLibre GeoJSON source/layers + box-drawing mode.
- `services/export.service.ts` → `ExportService` → Canvas capture with compass overlay and crop.
- `utils/minimap-compositor.ts` → Canvas 2D compositing for overview inset.
- `utils/tile-grid.ts` → Geographic grid subdivision for tile capture.
- `utils/report-sticky-defaults.ts` → `localStorage` persistence.

## Gotchas
- `saveStatus === 'saved'` ⟂ `wsApplyReportSessionUpdated` mutating `session$` — prevents clobbering local edits during catch-up replay.
- `isDrawingScene` synchronous getter exists for ESC handler; the Observable is not sufficient for synchronous checks.
- Custom scene export without `viewState` + `polygon` → `fitBounds` fallback, which may produce a different rotation than what the user drew.
- `captureRotatedSnip` uses DPR-scaled canvas pixels; `map.project()` returns CSS pixels, requiring multiplication by `canvas.width / clientWidth`.
- `waitForMapIdle` polls source cache tile loading state; a 200ms settle timer follows the last loading tile.
- Scene overlay layers are hidden during export capture and restored afterward. If capture throws, restoration happens in the tail after the try block.
- Tile grid caps at 50 occupied cells; large sites with dense entities may silently drop tiles beyond the cap.
- Overview capture omits the compass (`withCompass: false`) because it is a context thumbnail.
- `mergeClashScenes` preserves `accepted` and `notes` for matched IDs; custom scenes (`tier === 'custom'`) are always kept even if absent from refresh.
- `mergeZoneCoordination` matches rows by `_source_entity_id`; user-added rows (no `_source_entity_id`) are preserved, zones without user rows that disappear from refresh are dropped.
