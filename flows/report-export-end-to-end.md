---
trigger: { channel: ui, ref: "report export button" }
services: [ui, backend]
contracts: [ui-backend/http-contract]
external: [open_meteo, minio]
---

## Trigger
User clicks PDF or DOCX export in the report panel.

## Steps
1. `services/report-session.service.ts::ReportSessionService.startExport` forces save if `saveStatus === 'unsaved'` ⇒ emits `requestExport$` with `sessionId`, `format`, and `SceneDisplayOptions`.
2. Dashboard consumes `requestExport$` and calls `services/report-orchestrator.service.ts::ReportOrchestrator.onReportExport`.
3. Capture workflow:
   - Hide scene overlay layers; configure label/zone/building visibility per `displayOptions`.
   - Capture overview image via `captureOverviewForMinimap` (hides clutter layers; uses custom bounds or entity bounds).
   - Per accepted scene: restore `view_at` temporal state; if `viewState` + `polygon` exist, call `captureRotatedSnip` (restores draw-time bearing/zoom/center, projects polygon corners to DPR-scaled canvas pixels, crops to axis-aligned bbox); else `fitBounds` + `ExportService.captureMapWithCompass`.
   - If `showMinimap` enabled, `utils/minimap-compositor.ts::compositeMinimapIntoScene` composites overview inset with yellow highlight rect.
   - If tile subdivision enabled, `utils/tile-grid.ts::computeTileGridSummary` computes occupied cells (capped at 50), captures each tile, and `compositeGridOntoOverview` draws grid lines onto the overview image.
   - Restore map view, filters, labels, and overlay layers.
4. `ReportPanelComponent.doExport` delegates to `ReportSessionService.doExport`, which POSTs the captured blob via `ReportApi.exportPdf` or `exportDocx`.
5. Backend route `api/routes/report_routes.py` → `reports.py::export_pdf` or `export_docx` receives the request.
6. `services/report_pipeline.py::export_report` (or `report_export_orchestrator.py::resolve_export_context`) loads the session, verifies `report_manage` permission via `core/rbac.py::require_site_permission`, and resolves the template schema via `report_template_registry.py::get_template_schema`.
7. Context snapshot from session creation is used; for refresh, `report_context_refresh.py::refresh_live_sections` re-runs refreshable providers.
8. `services/report_providers.py` executes 6 hard-coded providers in fixed registration order: core → tokens → plants → clash_scenes → deliveries → permits. Later providers depend on keys set by earlier ones.
9. If the template includes a `weather_timeline` section, `report_export_orchestrator.py::fetch_weather_for_export` queries weather data from the Open-Meteo cache (short TTL, typically minutes).
10. `report_export_orchestrator.py::build_branding` fetches the site logo from Minio or falls back to a bundled asset.
11. Renderer selected by format:
    - Structured PDF: `report_document_renderer.py::render_pdf`
    - Comprehensive PDF: `pdf_renderer.py::PdfReportRenderer.render_full_report`
    - Structured DOCX: `report_document_renderer.py::render_docx`
    - Customer DOCX template: `report_docx_template_renderer.py::render_docx_from_template`
12. `services/report_rendering.py` performs PDF/DOCX rendering with Jinja2 templates.
13. Output bytes are returned directly in the HTTP response or stored in Minio.
14. Frontend receives the response blob and triggers a browser download via `URL.createObjectURL`.
15. On completion, the report session is carried forward for the next report generation.

## Side effects
- PATCH report session `form_data` to backend (forced save).
- POST export blob to `/api/reports/sessions/{id}/export/pdf` or `/docx`.
- Canvas capture and 2D compositing (`minimap-compositor`, `overview-grid-compositor`).
- MapLibre layer visibility and filter mutations during capture.
- DB reads for session, template, entities, clashes.
- Minio read for site logo; optional Minio write for stored export blob.
- Open-Meteo HTTP call for weather (cache with short TTL).
- Browser file download via `URL.createObjectURL`.
- Report session carry-forward for next report.

## Failure modes
- Auto-save PATCH fails ⇒ `_saveStatus` becomes `'error'`; export may proceed with stale data or fail.
- `captureRotatedSnip` DPR mismatch ⇒ incorrect crop dimensions if `canvas.width / clientWidth` diverges from `devicePixelRatio`.
- Tile grid > 50 occupied cells ⇒ silently capped at 50; large sites drop tiles beyond the cap.
- `saveStatus === 'saved'` blocks WebSocket session updates ⇒ in-flight edits are never clobbered, but stale committed state may persist.
- Missing session or template → 404 before rendering.
- Insufficient permissions → 403 via `core_rbac`.
- Weather service failure → silently omits weather section.
- Logo fetch failure → falls back to bundled asset.
- Invalid base64 main map image → 400; optional images skipped.
- Provider failure → logged and skipped; partial context rendered.
- Provider order is hard-coded; adding a provider requires understanding the dependency chain because later providers depend on keys set by earlier ones.
- Weather cache short TTL → repeated exports within the same hour re-fetch weather from Open-Meteo.
- Storage silent delete failures: `storage.py::delete_file_no_error` swallows all boto3 errors, masking cleanup issues.

## See also
- [frontend journey](../services/ui/flows/report-generation-export.md)
- [backend sequence](../services/backend/flows/report_export_flow.md)
- [HTTP contract](../contracts/ui-backend/http-contract.md)
