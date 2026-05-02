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

### RBAC silent failures in filtering
`get_site_contractor_filter` and `get_entity_visibility_filter` return `None` both when the user is an admin (no filter) and when the user has no verified membership (no access).
→ Callers cannot distinguish "show everything" from "show everything because no access" without re-checking membership.

### WebSocket stale permission caches
Cached `site_role`, `site_contractor_id`, and `can_view_others` on `WebSocketConnection` are set at subscribe time and NEVER auto-refreshed.
→ Any DB mutation that changes these MUST call `invalidate_subscription_context` or `invalidate_user_context`.

### Membership delete ordering
When removing a `SiteMembership`, call `invalidate_user_context` **before** deleting the row.
→ If you delete first, `_filter_event_for_user` will deny the `context_invalidated` event because the membership is gone.

### WebSocket ephemeral events are local-only
`broadcast_ephemeral` does NOT publish to Redis pub/sub.
→ In multi-process deployments, ephemeral drag/resize events only reach subscribers on the same worker.

### Unknown audience types fail closed
`_audience_admits` returns `False` for unrecognised `AudienceType` values.
→ Adding a new audience type without updating the handler silently drops all events using it.

### Redis pub/sub no auto-reconnect
If the Redis connection drops, the listener task exits and stays dead until `start()` is called again.
→ Cross-worker broadcasts stop until manual restart.

### Redis publish silently drops
`RedisPubSub.publish` returns without error if `_redis` is None.
→ Transient disconnects cause lost cross-worker broadcasts with only a one-time warning log.

### Redis event log clear() unguarded
`RedisEventLog.clear()` deletes all event and sequence keys globally.
→ No production guardrails; misuse causes complete event history loss.

### Data lock timezone stripping
`data_lock.py` normalises both datetimes to naive UTC before comparison.
→ If inputs are tz-aware but in different zones, ordering may be wrong for the same UTC instant.

## General

### WebSocket presence vs database presence
User may be present in WebSocket room but not reflected in database presence table if Redis is down and fallback event buffer overflows.
→ Do not rely solely on presence table for safety-critical checks.
