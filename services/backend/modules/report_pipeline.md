---
service: backend
summary: "Report export orchestration: PDF/DOCX generation with context resolution and weather"
paths: [backend/app/services/report/report_export_orchestrator.py, backend/app/services/report/report_context_service.py, backend/app/services/report/report_document_renderer.py, backend/app/services/report/report_template_registry.py, backend/app/services/report/report_data_assembler.py, backend/app/services/report/report_context_refresh.py]
flows: [services/backend/flows/report_export_flow.md]
touches: [postgis, minio]
external: [open_meteo]
last_verified_commit: TBD
---

# Report Pipeline

## Purpose
Coordinates report export workflow. Resolves template context, fetches weather data, assembles branding, and renders PDF or DOCX output.

## Interface
- `report_export_orchestrator.py::resolve_export_context(session_id, session, user, scene_images_raw)` → `(ReportSession, template_schema, scene_images)`
- `report_export_orchestrator.py::fetch_weather_for_export(report_session, template_schema, session)` → weather point dicts or `[]`
- `report_export_orchestrator.py::build_branding(session, report_session, template_schema)` → branding dict
- `report_template_registry.py::get_template_schema(session, template_id)` → dict or None
- `report_context_service.py::build_report_context(session, site_id, user, ...)` → context dict
- `report_document_renderer.py::render_pdf(template_schema, form_data, context_snapshot, ...)` → bytes
- `report_document_renderer.py::render_docx(template_schema, form_data, context_snapshot, ...)` → bytes
- `report_data_assembler.py::assemble_report_data(session, payload, site)` → FullReportData

## State
None. Stateless orchestration. All state in DB.

| State | Location | Notes |
|---|---|---|
| ReportSession | postgis | User's report configuration and context snapshot |
| Template schema | postgis | JSON schema defining sections and data providers |
| YAML template cache | process memory | Loaded once per process from `report_templates/` |

## Internals
- Template schema drives section assembly via provider registry
- Providers: `clash_context`, `deliveries_context`, `permits_context`, `plants_context`, `workers_context`
- Weather fetched only if template includes `weather_timeline` section
- Date range derived from `query_start`/`query_end` or `context_snapshot.date`
- Scene images passed as base64; resolved by `scene_id` lookup
- YAML templates cached in-memory; section library supports `include` directive resolution
- Zone spatial assignment uses PostGIS `ST_Intersects` in `report_context_service.py`
- Comprehensive PDF uses `pdf_renderer.py::PdfReportRenderer` with sub-renderers for tiles, tables, analytics
- Permission check uses `core/rbac.py::require_site_permission` → [core_rbac](core_rbac.md)
- User resolution via [core_auth](core_auth.md)
- Weather fetched via weather factory → external open_meteo
- Real-time events broadcast via `websocket_runtime` → [websocket_runtime](websocket_runtime.md)

## Touches
| Resource | How | Why |
|---|---|---|
| postgis | SQLModel / ST_Intersects | Report sessions, templates, entity data, zone assignment |
| minio | S3 | Stored report outputs, site logos |

## Gotchas
- Weather service unavailable → silently omits weather section
- Missing template → 404 before any rendering begins
- Large scene image payloads may hit request size limits
- Provider failure logged and skipped; downstream providers may see missing keys
