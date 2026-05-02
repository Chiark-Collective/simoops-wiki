---
service: backend
summary: "Report session lifecycle: creation, prefilling, carryforward, completion, refresh"
paths: [backend/app/services/report/report_session_service.py, backend/app/services/report/scene_decision_service.py, backend/app/services/report/report_session_carryforward.py, backend/app/services/report/report_form_prefiller.py, backend/app/services/report/report_session_serializer.py, backend/app/services/report/report_source_resolver.py, backend/app/services/report/report_context_refresh.py]
flows: [services/backend/flows/report_export_flow.md]
touches: [postgis]
external: []
last_verified_commit: TBD
---

# Report Session

## Purpose
Manages the full lifecycle of a report session from creation through completion, including form pre-filling, scene decision persistence, carry-forward from previous sessions, and live context refresh.

## Interface
- `report_session_service.py::ReportSessionService.create_session(user, site_id, template_id, template_schema, report_date, delivery_lookahead_days, query_start, query_end)` → ReportSession
- `report_session_service.py::ReportSessionService.update_session(report_session, form_data_patch)` → ReportSession
- `report_session_service.py::ReportSessionService.complete_session(user, report_session)` → ReportSession
- `report_session_service.py::ReportSessionService.refresh_context(user, report_session)` → dict
- `report_session_service.py::ReportSessionService.delete_session(report_session)` → None
- `report_session_service.py::ReportTemplateService.create_template(user, site_id, name, description, schema_def)` → ReportTemplate
- `scene_decision_service.py::persist_scene_decisions(session, report_session, user)` → list[SceneDecision]
- `report_session_carryforward.py::apply_carryforward(form_data, template_schema, site_id, template_id, session)` → dict
- `report_form_prefiller.py::prefill_form_data(template_schema, context)` → dict
- `report_session_serializer.py::session_to_read(report_session)` → ReportSessionRead
- `report_source_resolver.py::resolve_source(expression, context)` → Any
- `report_source_resolver.py::resolve_suggestions(expression, context)` → list[str]
- `report_context_refresh.py::refresh_live_sections(report_session, db_session, user)` → dict

## State
- `ReportSession` rows in postgis hold `form_data`, `context_snapshot`, `query_start`, `query_end`, `status`
- Status invariant: `draft` → `completed` is one-way; updates blocked after completion

## Internals
- Creation derives query bounds from `report_date` if not explicit → builds context via providers → prefills form → applies carryforward → persists → broadcasts `report_session` created event
- Form prefilling resolves dot-path source expressions with `[*]` wildcard expansion; supports `source_rows`, `iterate_over`, `group_title_source`
- Scene decisions extracted from `_scenes` keys in form_data on completion; auto-accepts critical/notable tiers, skips minor
- Carryforward copies non-empty rows from previous session's `carryforward: true` sections only if current section has no user-entered data
- Refresh re-runs `is_refreshable` providers, reassigns zones via PostGIS, returns section patches and context diffs
- Serialization converts `ReportSession` domain model to `ReportSessionRead` schema
- Source resolver strips `context.` prefix, supports nested wildcards like `zones[*].tokens[*].label`

## Touches
| Resource | How | Why |
|---|---|---|
| postgis | SQLModel | Session persistence, template storage |
| websocket_runtime | broadcast_config_event | Real-time session/decision events |

## Gotchas
- Carryforward silently skipped if no previous session exists
- Refresh mutates `context_snapshot` when `context_patch` is non-empty
- Scene decision persistence reads from every top-level form_data value containing `_scenes`
