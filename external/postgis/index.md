---
direction: both
consumed_by: [backend, keycloak]
auth: PostgreSQL native (user/password)
---

# PostGIS

## Use

| Consumer | Use |
|---|---|
| backend | Persistent entity data, planning cycles, clashes, reports, audits |
| keycloak | User and role persistence (optional; can use internal H2) |

## Resources

| Database | Purpose |
|---|---|
| `simoops` | Application data |
| `keycloak` | Identity data (when configured) |

## Extensions

- `postgis` — spatial types and operations
- `pg_trgm` — trigram similarity for text search

## Failure handling

- Backend uses SQLAlchemy async pool with retry on disconnect
- Long-running queries may timeout at application layer

## Quirks

- `pgdata` volume retains password after initialization; env changes have no effect
- PostGIS extension must be created per-database before spatial tables
- See [gotchas.md](../../gotchas.md)
