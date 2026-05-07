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
| 2026-05-02 | cf53fca | Cross-service end-to-end flows: 6 flows bridging frontend and backend | 6 cross-service flow pages + index updates |
| 2026-05-03 | f9606469 | Gotcha remediation ingest: cf53fca→f9606469 (38 commits, ~100 files). G3/G4 small fixes, G5 architectural cleanups, G7-G11 design-flag clusters, G12 auth observability. | 25 module updates + 6 new pages + gotchas reconciliation + glossary + indexes + shared files |
| 2026-05-07 | c56ee3d5 | Backend ingest: f9606469→c56ee3d5 (32 commits, 144 files). Auth diagnostics, contractor logo/branding, clash timeout+coalescing, RBAC split (site_settings_basic), WS invalidation on invite accept, health configurable thresholds, orphan feature versions migration. | 2 new modules + 14 updated backend pages + manifest + log |
| 2026-05-07 | c56ee3d5 | Frontend ingest: f9606469→c56ee3d5. Audit ghost hover preview, map source hardening (RecreatableMapSource caps), contractor branding on map (logos, POI pins, delivery pins, building badges), auth-diag integration, identity-scope last-site, 3-tab revision picker, delivery EntityStore refactor, clash debounce 1000ms. | 1 new module + 10 updated frontend pages + manifest + log |
| 2026-05-07 | c56ee3d5 | Cross-cutting ingest: f9606469→c56ee3d5. HTTP contract (diag, contractor logo, clash timeout, site PATCH), WebSocket contract (contractor:updated, entity_severity), auth contract (auth-diag), Keycloak branded theme + persistent data, Caddy static asset routes, glossary terms, gotchas (9 new entries). | 8 updated cross-cutting pages + manifest + log |
| 2026-05-07 | c56ee3d5 | Deployment documentation: Makefile targets, Docker Compose dev/prod, Netcup VPS, ngrok, backup/restore runbook | infra/compute.md, build.md, ops/backup-restore.md, infra/index.md, ops/index.md, gotchas.md |
| 2026-05-07 | c56ee3d5 | Production OOM investigation: dmesg analysis, docker stats, verified claims against docker-compose.prod.yml and backend/Dockerfile | analyses/oom-kill-cascade.md, index.md, gotchas.md, infra/compute.md, log.md |

## Next ingest targets

- Cross-service end-to-end flows complete — 6 flows bridging frontend and backend
- `ops/` runbooks for production incidents — backup/restore added
- `analyses/` for architectural decisions and explorations
- `infra/secrets.md` — environment variable management at infra level
- `infra/observability.md` — monitoring and alerting
