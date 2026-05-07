---
service: backend
summary: "FastAPI service: planning cycle, clash detection, entity management, reports"
paths: [backend/app/]
flows: [entity_creation, entity_update, vertex_op_flow, clash_detect_and_resolve, planning_cycle_lifecycle, planning_submission_flow, bulk_import_flow, permit_import_flow, report_export_flow, geometry_cut_flow, floor_plan_upload_flow, invite_accept_flow]
external: [keycloak, postgis, minio, titiler, redis, open_meteo]
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

# Backend

## Routing Table

### API

| Page | What |
|---|---|
| [api/http.md](api/http.md) | HTTP routes |
| [api/websocket.md](api/websocket.md) | WebSocket events |

### Core Modules

| Page | What |
|---|---|
| [modules/core_auth.md](modules/core_auth.md) | JWT authentication and user resolution |
| [modules/core_rbac.md](modules/core_rbac.md) | Site-scoped permissions and role hierarchy |
| [modules/websocket_runtime.md](modules/websocket_runtime.md) | WebSocket connections, rooms, and presence |
| [modules/redis_core.md](modules/redis_core.md) | Redis pub/sub relay and event log |
| [modules/data_lock.md](modules/data_lock.md) | Site-level data immutability boundary |
| [modules/event_log.md](modules/event_log.md) | Redis-backed sequenced event log |
| [modules/presence_manager.md](modules/presence_manager.md) | WebSocket presence state machine |
| [modules/config.md](modules/config.md) | Pydantic settings from `SIMOOPS_*` env vars |
| [modules/jwks.md](modules/jwks.md) | Keycloak JWKS client for RS256 validation |
| [modules/permissions.md](modules/permissions.md) | Permission enum and role-to-permission mapping |
| [modules/storage.md](modules/storage.md) | S3-compatible object storage abstraction |
| [modules/storage_sweep.md](modules/storage_sweep.md) | Background retry sweep for failed S3 deletions |
| [modules/logo_normalisation.md](modules/logo_normalisation.md) | Logo normalisation for map rendering (PNG→512px, SVG passthrough) |

### Entity Management

| Page | What |
|---|---|
| [modules/entity_service.md](modules/entity_service.md) | Entity CRUD, copy, snapshots |
| [modules/entity_broadcast_audit.md](modules/entity_broadcast_audit.md) | Broadcast, audit, revert, timeline |
| [modules/entity_schedule.md](modules/entity_schedule.md) | Temporal scheduling and shift resolution |
| [modules/vertex_op.md](modules/vertex_op.md) | OT polygon vertex editing |
| [modules/plant_service.md](modules/plant_service.md) | Plant CRUD, geometry, scheduling, clash colors |
| [modules/worker_service.md](modules/worker_service.md) | Worker CRUD, position, radius, schedule, copy |
| [modules/alert_service.md](modules/alert_service.md) | Alert CRUD, activity tracking, resolution |
| [modules/delivery_service.md](modules/delivery_service.md) | Delivery CRUD, contractor assignment, windows |
| [modules/poi_service.md](modules/poi_service.md) | Point-of-interest map markers |
| [modules/text_label_service.md](modules/text_label_service.md) | Text annotation CRUD for maps |
| [modules/audit_revert_service.md](modules/audit_revert_service.md) | Revert entities to previous audit snapshots |

### Site & Organization

| Page | What |
|---|---|
| [modules/site_service.md](modules/site_service.md) | Site CRUD, cascade delete, default-shift seeding |
| [modules/contractor_service.md](modules/contractor_service.md) | Contractor CRUD with dependency checks |
| [modules/shift_service.md](modules/shift_service.md) | Shift definition CRUD |
| [modules/membership_service.md](modules/membership_service.md) | SiteMembership approval / rejection |
| [modules/smart_group_service.md](modules/smart_group_service.md) | Query definitions, per-event audience routing |

### Clash Detection

| Page | What |
|---|---|
| [modules/clash_engine.md](modules/clash_engine.md) | Declarative clash engine |
| [modules/clash_detection.md](modules/clash_detection.md) | Runtime detection, resolution, caching |
| [modules/clash_rules.md](modules/clash_rules.md) | Rule CRUD, versions, profiles, DSL |
| [modules/clash_proximity.md](modules/clash_proximity.md) | Proximity engine and spatial predicates |
| [modules/clash_at_time_service.md](modules/clash_at_time_service.md) | Historical clash detection at wall-clock instant |
| [modules/clash_cache.md](modules/clash_cache.md) | Redis/in-memory caching for clash results |
| [modules/clash_resolution_service.md](modules/clash_resolution_service.md) | Resolution workflow with comments |
| [modules/clash_scene_scoring.md](modules/clash_scene_scoring.md) | Scene-level scoring, ranking, severity aggregation |
| [modules/rule_profile_service.md](modules/rule_profile_service.md) | Profile CRUD, activation, cloning, templates |
| [modules/rule_version_service.md](modules/rule_version_service.md) | Rule versioning and rollback |

### Planning Cycle

| Page | What |
|---|---|
| [modules/planning_cycle.md](modules/planning_cycle.md) | Planning cycle lifecycle |
| [modules/planning_compare.md](modules/planning_compare.md) | Compare, carry-forward, actualize |
| [modules/planning_submission.md](modules/planning_submission.md) | Submissions, dedup, snapshots, insights |

### Reports

| Page | What |
|---|---|
| [modules/report_pipeline.md](modules/report_pipeline.md) | Report export orchestration |
| [modules/report_providers.md](modules/report_providers.md) | Context providers and registration order |
| [modules/report_session.md](modules/report_session.md) | Session lifecycle and carry-forward |
| [modules/report_rendering.md](modules/report_rendering.md) | PDF/DOCX rendering pipeline |

### Import & Export

| Page | What |
|---|---|
| [modules/bulk_import.md](modules/bulk_import.md) | CSV/GeoJSON bulk ingest |
| [modules/permit_import.md](modules/permit_import.md) | XLSX permit parsing |
| [modules/bundle_import.md](modules/bundle_import.md) | .sob bundle ingest |
| [modules/export_service.md](modules/export_service.md) | GeoJSON and table export |

### Maps, Geometry & Weather

| Page | What |
|---|---|
| [modules/geometadata.md](modules/geometadata.md) | GeoJSON/SHP feature management |
| [modules/geometry_cutting.md](modules/geometry_cutting.md) | Polygon cutting and floor plans |
| [modules/site_maps.md](modules/site_maps.md) | COG tiles and map layers |
| [modules/weather_service.md](modules/weather_service.md) | Open-Meteo integration |

### Auth

| Page | What |
|---|---|
| [modules/auth_invites.md](modules/auth_invites.md) | Email invites and invite links |
| [modules/auth_diag.md](modules/auth_diag.md) | Unauthenticated telemetry sink for frontend auth diagnostics |

### Flows

| Page | What |
|---|---|
| [flows/entity_creation.md](flows/entity_creation.md) | End-to-end entity creation |
| [flows/entity_update.md](flows/entity_update.md) | Entity PATCH/PUT with audit |
| [flows/vertex_op_flow.md](flows/vertex_op_flow.md) | Collaborative polygon editing |
| [flows/clash_detect_and_resolve.md](flows/clash_detect_and_resolve.md) | Clash detection and broadcast |
| [flows/planning_cycle_lifecycle.md](flows/planning_cycle_lifecycle.md) | Draft -> active -> archive |
| [flows/planning_submission_flow.md](flows/planning_submission_flow.md) | Submit -> compare -> approve/reject |
| [flows/bulk_import_flow.md](flows/bulk_import_flow.md) | CSV/GeoJSON bulk import |
| [flows/permit_import_flow.md](flows/permit_import_flow.md) | XLSX permit import |
| [flows/report_export_flow.md](flows/report_export_flow.md) | Report export sequence |
| [flows/geometry_cut_flow.md](flows/geometry_cut_flow.md) | Geometry cut and broadcast |
| [flows/floor_plan_upload_flow.md](flows/floor_plan_upload_flow.md) | Floor plan upload and tile generation |
| [flows/invite_accept_flow.md](flows/invite_accept_flow.md) | Invite link to site membership |

## Entry Points

- HTTP API on port 8000
- WebSocket on `/ws` for real-time events
- Async tasks via background workers (shifts, weather, exports)

## Architecture

| Layer | Path |
|---|---|
| API routes | `api/routes/` |
| Services | `services/` |
| Engine | `engine/` |
| Models | `models/` |
| Core | `core/` |

## Touches

| Resource | How | Why |
|---|---|---|
| postgis | SQLAlchemy / SQLModel | Persistent data |
| redis | cache, pub/sub, presence | Ephemeral state, real-time |
| keycloak | OIDC validation | Authentication |
| minio | S3 API | Image/object storage |
| titiler | HTTP | Tile rendering |
| open_meteo | HTTP | Weather forecasts |
