---
---

# Log

Ingest history and manifest reference.

## Manifest

Source of truth for tracked sources: [manifest.json](manifest.json)

## History

| Date | Commit | Scope | Pages touched |
|---|---|---|---|
| 2026-05-02 | a436901 | Phase 2 pilot (backend) | Initial scaffold: AGENTS.md, index.md, topology.md, log.md, glossary.md, gotchas.md, services/backend/*, infra/*, external/* |
| 2026-05-02 | 857e514 | Pass 1: core_auth | services/backend/modules/core_auth.md, services/backend/index.md, glossary.md, gotchas.md, manifest.json |
| 2026-05-02 | d4224c0 | Pass 1: core_rbac, websocket, redis, data_lock | services/backend/modules/core_rbac.md, services/backend/modules/websocket_runtime.md, services/backend/modules/redis_core.md, services/backend/modules/data_lock.md, services/backend/index.md, glossary.md, gotchas.md, manifest.json |
| 2026-05-02 | 0cf57fb | Pass 2: API inventory (http, websocket) | services/backend/api/http.md, services/backend/api/websocket.md, log.md, manifest.json |
| 2026-05-02 | 4183b2f | Pass 3: Domain deep dives — all 7 batches (Entity, Clash, Planning, Import/Export, Reports, Maps/Geometry/Weather, Auth/Core) | 29 modules + 12 flows + shared files |
| 2026-05-02 | cf53fca | Source repo pulled to cf53fca (permits.py changes, permit API tests) | Manifest head commit updated |
| 2026-05-02 | TBD | Pass 4: Remaining backend modules — Batches H, I, J, K (Core Entities, Site & Org, Clash Depth, Core Infrastructure) | 22 modules + shared files |
| 2026-05-02 | TBD | Phase 1 (frontend): Scaffold — 19 UI module stubs + 2 API channels + index + shared files | 24 pages + shared files |
| 2026-05-02 | cf53fca | Cross-service mapping pass: HTTP, WebSocket, Auth contracts | 3 contract pages + index updates |
| 2026-05-02 | cf53fca | Frontend Phase 2 Batch A: app-shell, auth, shared-ui, dashboard deep dives | 4 UI module pages |
| 2026-05-02 | cf53fca | Frontend Phase 2 Batch B: entity-store, selection, realtime-sync deep dives | 3 UI module pages |
| 2026-05-02 | cf53fca | Frontend Phase 2 Batch C: map-core, map-layers, map-interaction, map-visuals, map-floor-plans deep dives | 5 UI module pages |
| 2026-05-02 | cf53fca | Frontend Phase 2 Batch D: entity-creation, entity-edit, entity-delete deep dives | 3 UI module pages |
| 2026-05-02 | cf53fca | Frontend Phase 2 Batch E: temporal-planning, clash-ui, site-admin, reports deep dives | 4 UI module pages |
| 2026-05-02 | cf53fca | Frontend flows: 12 user journey flows documented via parallel subagents | 12 flow pages + index updates |

## Next ingest targets

- Frontend flows complete — 12 user journeys documented
- Cross-service end-to-end flows (combine frontend + backend pairs)
- `ops/` runbooks for production incidents
- `analyses/` for architectural decisions and explorations
