---
service: backend
summary: "Report export orchestration: PDF/DOCX generation with context resolution and weather"
paths: [backend/app/services/report/report_export_orchestrator.py, backend/app/services/report/report_context_service.py, backend/app/services/report/report_document_renderer.py]
flows: []
touches: [postgis, minio]
external: [open_meteo]
last_verified_commit: TBD
---

# Report Pipeline

## Purpose

Coordinates report export workflow. Resolves template context, fetches weather data, assembles branding, and renders PDF or DOCX output.

## Interface

- `resolve_export_context(session_id, session, user, scene_images_raw)` → `(ReportSession, template_schema, scene_images)`
- `fetch_weather_for_export(report_session, template_schema, session)` → weather point dicts or `[]`
- `ReportDocumentRenderer.render(report_session, context, format)` → bytes

## State

None. Stateless orchestration. All state in DB.

| State | Location | Notes |
|---|---|---|
| ReportSession | postgis | User's report configuration and context snapshot |
| Template schema | postgis | JSON schema defining sections and data providers |

## Internals

- Template schema drives section assembly via provider registry
- Providers: `clash_context`, `deliveries_context`, `permits_context`, `plants_context`, `workers_context`
- Weather fetched only if template includes `weather_timeline` section
- Date range derived from `query_start`/`query_end` or `context_snapshot.date`
- Scene images passed as base64; resolved by `scene_id` lookup

## Touches

| Resource | How | Why |
|---|---|---|
| postgis | SQLModel | Report sessions, templates, entity data |
| minio | S3 | Stored report outputs |

## Gotchas

- Weather service unavailable → silently omits weather section
- Missing template → 404 before any rendering begins
- Large scene image payloads may hit request size limits
