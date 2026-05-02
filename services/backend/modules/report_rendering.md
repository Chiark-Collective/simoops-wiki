---
service: backend
summary: "PDF/DOCX rendering: structured documents and comprehensive map reports"
paths: [backend/app/services/report/report_document_renderer.py, backend/app/services/report/pdf_renderer.py, backend/app/services/report/report_docx_template_renderer.py, backend/app/services/report/pdf_page_scaffold.py, backend/app/services/report/pdf_table_renderer.py, backend/app/services/report/pdf_summary_renderer.py, backend/app/services/report/pdf_analytics_renderer.py, backend/app/services/report/pdf_tile_renderer.py, backend/app/services/report/report_pdf_sections.py, backend/app/services/report/report_pdf_styles.py, backend/app/services/report/report_data_assembler.py, backend/app/services/report/report_context_service.py]
flows: [services/backend/flows/report_export_flow.md]
touches: [postgis, minio]
external: [open_meteo]
last_verified_commit: TBD
---

# Report Rendering

## Purpose
Renders completed report sessions into PDF or DOCX documents. Two rendering paths exist: a structured document renderer for generic template-based reports, and a comprehensive map-centric renderer for site reports with tiles, clashes, and analytics.

## Interface
- `report_document_renderer.py::render_pdf(template_schema, form_data, context_snapshot, weather_points, scene_images, branding, tile_images)` → bytes
- `report_document_renderer.py::render_docx(template_schema, form_data, context_snapshot, weather_points, scene_images, branding)` → bytes
- `pdf_renderer.py::PdfReportRenderer.render_simple_report(data)` → bytes
- `pdf_renderer.py::PdfReportRenderer.render_full_report(data)` → bytes
- `report_docx_template_renderer.py::render_docx_from_template(template_bytes, context, form_data)` → bytes
- `report_data_assembler.py::assemble_report_data(session, payload, site)` → FullReportData

## State
None. Stateless rendering pipeline.

## Internals
- `report_document_renderer.py` uses ReportLab Platypus/SimpleDocTemplate for structured PDF; python-docx for DOCX
- `pdf_renderer.py` uses ReportLab canvas directly for the comprehensive report with map views
- `pdf_page_scaffold.py` draws header/footer/title page chrome; deferred-save footer shows "X of Y" page numbers
- `pdf_tile_renderer.py` renders overview maps, detail tiles with sidebars, isometric views; supports cluster tiles and pre-captured tiles
- `pdf_table_renderer.py` paginates clash and entity tables; severity-colored row backgrounds; nested entity tables for clash rows
- `pdf_summary_renderer.py` draws statistics summary and weather timeline pages
- `pdf_analytics_renderer.py` draws pie charts, bar charts, and cross-contractor clash matrix
- `report_pdf_sections.py` renders individual section types for the document renderer: metadata, table, narrative, dynamic_group, weather_timeline, scene_selection, overview_page, tile_grid
- `report_pdf_styles.py` bundles seven ParagraphStyle instances into `ReportPdfStyles`
- `report_data_assembler.py` decodes base64 images (releasing source strings to reduce memory), loads temporal entities, computes clashes, builds formatted rows, fetches weather
- `report_docx_template_renderer.py` fills Jinja2 placeholders in customer-provided DOCX templates using docxtpl; `form_data` overrides `context`

## Touches
| Resource | How | Why |
|---|---|---|
| postgis | SQLModel | Entity loading for comprehensive PDF |
| minio | S3 | Logo bytes fetch |
| open_meteo | HTTP | Weather timeline data |

## Gotchas
- Invalid main map image → 400; corrupt optional images skipped
- Base64 source strings released immediately after decode to reduce peak memory
- DOCX/PIL image processing failures skip the image and continue rendering
- Customer-provided DOCX templates that are not valid docx raise ValueError
