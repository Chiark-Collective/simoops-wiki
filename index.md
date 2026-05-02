---
wiki: simoops
source_repo: /Users/williamcheung/Development/simoops
---

# SimOops Wiki

System knowledge for the SimOops platform.

## Topology

See [topology.md](topology.md) for runtime boundaries and data flow.

## Services

| Service | Role | Entry |
|---|---|---|
| [backend](services/backend/index.md) | API, planning cycle, clash detection, reports | HTTP, WebSocket |
| ui | Angular SPA, map, dashboard | HTTP (static) |

## Cross-service

- [Flows](flows/) — end-to-end sequences
- [Contracts](contracts/) — inter-service data contracts
- [External systems](external/) — Keycloak, PostGIS, Minio, TiTiler, Redis
- [Infra](infra/) — data stores, network, compute
- [Ops](ops/) — runbooks keyed on symptoms
- [Build](build.md) — CI/CD

## Reference

- [Glossary](glossary.md)
- [Gotchas](gotchas.md)
- [Log](log.md)
