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

## Next ingest targets

- `services/backend/modules/core_rbac.md` — site-scoped permissions and role hierarchy
- `services/backend/modules/websocket_runtime.md` — connection registry, rooms, broadcast filtering
- `services/backend/modules/redis_core.md` — pub/sub and ephemeral state
- `services/backend/modules/data_lock.md` — site-level admin locks
- `services/backend/api/http.md` — exhaustive API inventory (Pass 2)
