---
---

# Gotchas

## Infrastructure

### PostGIS password immutability
Once `pgdata` is initialized, changing `POSTGRES_PASSWORD` in env has no effect.
The data directory retains the original password.
→ Rotate via `ALTER USER` or rebuild volume.

### Keycloak redirect URI loss
Keycloak container restart without persistent `kc_data` loses configured redirect URIs.
→ Externalize realm config or mount persistent volume.

### Keycloak OOM
Keycloak fails at 1 GB limit.
→ Allocate ≥2 GB in production.

## Backend

### Contractor tokens deprecated
Contractor tokens (`sub` prefix `"contractor:"`) are rejected with 401 in all auth paths.
→ Use Keycloak OIDC login only.

### Planning cycle state transitions
Some transitions are irreversible (e.g., active → archived).
→ Validate before applying; no rollback path in current implementation.

### Clash engine recomputation scope
Clash detection recomputes per site + shift + time slice.
→ Large sites with many tokens may trigger expensive recalculations on every entity mutation.

## General

### WebSocket presence vs database presence
User may be present in WebSocket room but not reflected in database presence table if Redis is down and fallback event buffer overflows.
→ Do not rely solely on presence table for safety-critical checks.
