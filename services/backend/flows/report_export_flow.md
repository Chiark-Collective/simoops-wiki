---
trigger: { channel: http, ref: "POST /api/reports/{session_id}/export" }
services: [backend]
contracts: []
external: [open_meteo, minio]
---

# Report Export Flow

## Trigger
HTTP POST to export a report session as PDF or DOCX.

## Steps
1. Route receives `session_id` and optional `scene_images_raw`
2. `report_export_orchestrator.py::resolve_export_context` loads session, verifies `report_manage` permission via `core/rbac.py::require_site_permission`, resolves template schema
3. `report_template_registry.py::get_template_schema` checks built-in YAML cache first, then falls back to DB
4. Context snapshot from session creation is used; for refresh, `report_context_refresh.py::refresh_live_sections` re-runs refreshable providers
5. Providers execute in registry order: core → tokens → plants → clash_scenes → deliveries → permits
6. `report_export_orchestrator.py::fetch_weather_for_export` queries weather timeline if template includes `weather_timeline` section
7. `report_export_orchestrator.py::build_branding` fetches site logo from minio or falls back to bundled asset
8. For comprehensive PDF: `report_data_assembler.py::assemble_report_data` loads entities, decodes images, computes clashes, builds tables
9. Renderer selected by format:
   - Structured PDF: `report_document_renderer.py::render_pdf`
   - Comprehensive PDF: `pdf_renderer.py::PdfReportRenderer.render_full_report`
   - Structured DOCX: `report_document_renderer.py::render_docx`
   - Customer DOCX template: `report_docx_template_renderer.py::render_docx_from_template`
10. Output bytes returned to client or stored in minio

## Side effects
- DB reads for session, template, entities, clashes
- Minio read for site logo
- Optional Open-Meteo HTTP call for weather
- Report output bytes generated; caller persists to minio or streams to client

## Failure modes
- Missing session → 404 before rendering
- Missing template → 404 before rendering
- Insufficient permissions → 403 via `core_rbac`
- Weather service failure → silently omits weather section
- Logo fetch failure → falls back to bundled asset
- Invalid base64 main map image → 400; optional images skipped
- Provider failure → logged and skipped; partial context
