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
| 2026-05-02 | TBD | Pass 1: core_rbac, websocket, redis, data_lock | services/backend/modules/core_rbac.md, services/backend/modules/websocket_runtime.md, services/backend/modules/redis_core.md, services/backend/modules/data_lock.md, services/backend/index.md, glossary.md, gotchas.md, manifest.json |

## Next ingest targets

- `services/backend/api/http.md` — exhaustive API inventory (Pass 2)
- `services/backend/api/websocket.md` — WebSocket event surface (Pass 2)
- `services/backend/modules/clash_engine.md` — refresh with cross-references to core modules
- `services/backend/modules/planning_cycle.md` — refresh with cross-references to core modules
- `services/backend/flows/entity_creation.md` — trace through auth → rbac → websocket → redis
