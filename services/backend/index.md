---
service: backend
summary: "FastAPI service: planning cycle, clash detection, entity management, reports"
paths: [backend/app/]
flows: [entity_creation, clash_detect_and_resolve]
external: [keycloak, postgis, minio, titiler, redis]
last_verified_commit: TBD
---

# Backend

## Routing Table

| Page | What |
|---|---|
| [api/http.md](api/http.md) | HTTP routes |
| [api/websocket.md](api/websocket.md) | WebSocket events |
| [modules/core_auth.md](modules/core_auth.md) | JWT authentication and user resolution |
| [modules/clash_engine.md](modules/clash_engine.md) | Declarative clash detection |
| [modules/planning_cycle.md](modules/planning_cycle.md) | Planning cycle lifecycle |
| [modules/report_pipeline.md](modules/report_pipeline.md) | Report export orchestration |
| [flows/entity_creation.md](flows/entity_creation.md) | End-to-end entity creation |
| [flows/clash_detect_and_resolve.md](flows/clash_detect_and_resolve.md) | Clash detection flow |

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
