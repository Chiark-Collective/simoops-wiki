---
trigger: { channel: ui, ref: "report export button" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User opens the report panel and initiates report generation and export.

## Steps
1. `dashboard/report-panel/report-panel.component.ts::ReportPanelComponent` opens ⇒ `services/report-session.service.ts::ReportSessionService.open(siteId)` loads templates, drafts, and completed sessions via `api/report.api.ts::ReportApi`.
2. User selects a template ⇒ `ReportSessionService.startNewSession` POSTs `ReportSessionCreate` to backend ⇒ receives `ReportSession` with `context_snapshot` ⇒ switches `view$` to `'form'`.
3. `components/report-wizard/report-section-scene-selection.component.ts::ReportSectionSceneSelectionComponent` renders clash scenes. User toggles accept/reject, hovers, or clicks focus ⇒ `services/report-orchestrator.service.ts::ReportOrchestrator` attaches and updates `map/map-scene-overlay.ts::MapSceneOverlay` with GeoJSON fill/outline layers.
4. User draws a custom scene on the map ⇒ `ReportOrchestrator.onReportDrawCustomScene` calls `MapSceneOverlay.startDrawing` ⇒ on completion, `ReportPanelComponent.addCustomScene` delegates to `ReportSessionService.addCustomScene`, which appends a `tier === 'custom'` scene and calls `setSceneData`.
5. Any section change ⇒ `ReportSessionService.setSectionData` updates `_formData`, sets `_saveStatus` to `'unsaved'`, and pushes to `saveSubject`. A `debounceTime(2000)` pipeline PATCHes `form_data` via `ReportApi` ⇒ `_saveStatus` becomes `'saved'` ⇒ `persistStickyDefaults` writes to `localStorage`.
6. `services/report-session-sync-binding.service.ts::ReportSessionSyncBinding` routes WebSocket `report_session` `updated` events to `ReportSessionService.wsApplyReportSessionUpdated`. `saveStatus === 'saved'` ⟂ mutation of `_session` — in-flight edits are never clobbered.
7. `ReportSessionService.setupLiveRefresh` subscribes to `entityService.tokens$`, `plants$`, and `clashState.clashes$` with `skip(1)` + `debounceTime(7000)` ⇒ POSTs `refresh-context` ⇒ merges results via `utils/report-merge.ts::mergeClashScenes` and `mergeZoneCoordination`, preserving user edits and custom scenes.
8. User clicks PDF/DOCX export ⇒ `ReportSessionService.startExport` forces a save if `saveStatus === 'unsaved'` ⇒ emits `requestExport$` with `sessionId`, `format`, and `SceneDisplayOptions`.
9. Dashboard receives `requestExport$` and calls `ReportOrchestrator.onReportExport`. Capture workflow:
   - Hide scene overlay layers; configure label/zone/building visibility per `displayOptions`.
   - Capture overview image via `captureOverviewForMinimap` (hides clutter layers; uses custom bounds or entity bounds).
   - Per accepted scene: restore `view_at` temporal state; if `viewState` + `polygon` exist, call `captureRotatedSnip` (restores draw-time bearing/zoom/center, projects polygon corners to DPR-scaled canvas pixels, crops to axis-aligned bbox); else `fitBounds` + `ExportService.captureMapWithCompass`.
   - If `showMinimap` enabled, `utils/minimap-compositor.ts::compositeMinimapIntoScene` composites overview inset with yellow highlight rect.
   - If tile subdivision enabled, `utils/tile-grid.ts::computeTileGridSummary` computes occupied cells (capped at 50), captures each tile, and `compositeGridOntoOverview` draws grid lines onto the overview image.
   - Restore map view, filters, labels, and overlay layers.
10. `ReportPanelComponent.doExport` delegates to `ReportSessionService.doExport`, which POSTs the blob via `ReportApi.exportPdf` or `exportDocx` and triggers a browser download via `downloadBlob`.
11. On session load/resume, `applyStickyDefaults` reads `localStorage` per site and injects missing front-matter values.

## Side effects
- PATCH report session `form_data` to backend.
- POST `refresh-context` and merge updated sections into `_formData`.
- POST export blob requests (`/reports/sessions/{id}/export/pdf` or `/docx`).
- Canvas capture and 2D compositing (`minimap-compositor`, `overview-grid-compositor`).
- `localStorage` read/write for sticky defaults.
- MapLibre layer visibility and filter mutations during capture.
- BehaviorSubject state mutations (`session$`, `formData$`, `saveStatus$`, `scenesChanged$`).
- Browser file download via `URL.createObjectURL`.

## Failure modes
- Auto-save PATCH fails ⇒ `_saveStatus` becomes `'error'`; local typing continues but changes are not persisted.
- WebSocket `updated` arrives while `saveStatus === 'unsaved'` ⇒ `_session` is not updated; stale committed state remains until next successful save.
- Scene capture throws ⇒ overlay layers and map view may not be restored within the try block; restoration follows the catch but temporal state (`viewDateTime`) is restored unconditionally.
- `captureRotatedSnip` DPR mismatch ⇒ incorrect crop dimensions if `canvas.width / clientWidth` diverges from `devicePixelRatio`.
- Tile grid > 50 occupied cells ⇒ silently capped at 50; large sites drop tiles beyond the cap.
- Custom scene without `viewState` + `polygon` ⇒ falls back to `fitBounds` with different rotation than the draw-time view.
- `mergeClashScenes` drops non-custom scenes absent from refresh; custom scenes are always preserved.
- `mergeZoneCoordination` drops zones without matching `_source_entity_id` and without user-added rows.
- Map idle timeout during capture ⇒ `waitForMapIdle` polls source cache tile loading state and may stall if tiles never finish loading.
