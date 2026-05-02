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

### Entity broadcast used by planning for clash invalidation
`entity_broadcast.py::invalidate_clash_cache` is imported by planning services (`actualize_service.py`, `submission_service.py`, `submission_snapshot_service.py`).
→ Tight coupling between entity broadcast and planning; modifying broadcast internals may break planning.

### Schedule reconcile drops orphaned occurrences
`schedule_reconcile.py` removes occurrences that no longer match any shift window.
→ Clients may see entities disappear from shifts without an explicit delete event.

### Vertex op buffer overflow
`vertex_op_buffer.py` has a fixed-size ring buffer for pending ops.
→ High-frequency edits from multiple users may evict ops before they are persisted.

### Clash cache generation mismatch
`clash_cache.py` keys results by `(site_id, shift_id, generation)`. If generation is incremented but cache is not cleared, stale results are served.
→ Always invalidate cache when incrementing generation.

### Planning baseline re-import is not always idempotent
`import_baseline_service.py` shadows baseline rows. Re-running on a cycle with native modifications may create duplicates or lose edits.
→ Re-import is safe only on fresh cycles.

### Report provider order is hard-coded
`providers/registry.py` registers providers in a fixed order. Later providers depend on keys set by earlier ones.
→ Adding a new provider requires understanding the dependency chain and inserting at the correct position.

### Weather cache short TTL
`weather/cache.py` caches Open-Meteo responses with a short TTL (typically minutes).
→ Repeated report exports within the same hour re-fetch weather.

### Presence heartbeat required
`presence_manager.py` drops users whose heartbeat expires.
→ Clients that stop sending `presence_heartbeat` will disappear from the presence list even if the WebSocket is still connected.

### Pre-migration audit entries cannot be reverted
`AuditRevertService` raises HTTP 400 when the target `AuditLog.snapshot` is `None`.
→ Any audit row written before the snapshot column was backfilled is non-revertible.

### Audit-revert geometry SRID fallback
`_deserialize_field_value` defaults to `srid=3857` when the SQLAlchemy `Geometry` column has no explicit srid.
→ If a layer stores geometries in a different projection, reverts silently inject the wrong SRID.

### Text label delete bypasses broadcast helper
`text_label_service.py::delete_text_label` calls `ws_manager.broadcast_entity_event` directly instead of `_broadcast_event`.
→ If broadcast payload formatting changes, deletion may drift from create/update.

### JWKS stale cache on prolonged outage
`jwks.py::get_jwks` serves stale cache when the Keycloak endpoint is unreachable.
→ Key rotation during an outage causes token validation failures until the endpoint recovers.

### JWKS relaxed issuer boundary
`decode_keycloak_token` disables issuer verification (`verify_iss: False`).
→ Tokens from any realm sharing the same Keycloak instance could pass signature validation; only the audience check remains.

### Storage health transient false negatives
`storage.py::check_health` returns `False` on `OSError`.
→ DNS blips or temporary network issues appear as permanent unhealthiness in readiness probes.

### Storage silent delete failures
`storage.py::delete_file_no_error` swallows all `BotoCoreError` and `ClientError`.
→ Cleanup paths may leave orphaned objects without any signal.

## Frontend

### Zone.js + MapLibre symbol-layer corruption
GeoJSON sources that start empty and are later populated via `setData` silently fail for symbol layers (`queryRenderedFeatures` returns zero results). Affected sources: delivery pins, inactive cranes, building badges, geometadata.
→ Use `updateGeoJsonSourceWithRecreate` on the first empty→populated transition; afterwards re-apply visibility and selection state.

### MapLibre handlers fire outside Angular zone
`ngZone.runOutsideAngular` during map construction is required for 60fps performance, but all pointer/drag/hover handlers fire outside the zone. `markForCheck` races under worker contention; signals or explicit `detectChanges` are required in map-driven components.

### AuthService test token read once at construction
`window.__SIMOOPS_TEST_TOKEN__` is read in the `AuthService` constructor. Injecting it after bootstrap has no effect.
→ Set the token before `bootstrapApplication` resolves.

### UserService removes pending invite before API resolves
`fetchCurrentUser` deletes `simoops_pending_invite_token` from `localStorage` before `acceptInviteLink` resolves. If the API fails, the token is lost and the user must re-enter the invite link.

### Dashboard wiring subscriptions are app-scoped
`DashboardBootstrapWiringService` and `DashboardInteractionWiringService` are `providedIn: 'root'` with `takeUntilDestroyed` bound to the app-scoped `DestroyRef`. If the dashboard component is ever recreated, subscriptions leak.

### PanelStateService silently swallows parse failures
`loadLayoutPrefs` returns `{}` on any `JSON.parse` error, causing a full fallback to `DEFAULT_UI_STATE`. Invalid individual fields are also silently dropped.

### WebSocket catch-up dedup races with live events
`pendingCatchUpSnapshot` is frozen at `sendCatchUp` time. If a live broadcast arrives after send but before the response with `seq > snapshot`, the snapshot threshold prevents silent dropping of legitimately missed events. See `websocket.service.ts::sendCatchUp` "C2 regression" comment.

### Offline queue optimistic state may drift
`executeMutation` calls `EntityService.addLocal/updateLocal/removeLocal` optimistically. If the API succeeds but the WS broadcast is delayed, local state may be temporarily out of sync with the server seq.

### Map source recreation resets filters and layout properties
`recreateGeoJsonSource` removes and re-adds the source and its layers. Dynamic `setLayoutProperty`, `setFilter`, and `setFeatureState` changes are lost. Callers must re-apply them after recreation.

### SiteContextService getters return new Observable references
`selectedShift$` and `selectedDate$` are getters returning `TemporalContextService` observables. Binding directly in templates creates a new reference each change-detection cycle; cache in a component property or use `siteContext.context$`.

### Sync bindings must be injected eagerly
`ContractorSyncBinding`, `ShiftSyncBinding`, `InviteSyncBinding`, and others must be injected before the first WS broadcast arrives. Lazy injection (e.g., behind `*ngIf`) misses early events.

### EntityStore optimistic updates only for tokens and plants
`updateArea` lacks optimistic-update and 409-rollback logic. Area edits are not protected from concurrent modification conflicts.

### Revision mode bypasses plan-state filter
If `RevisionModeService` is enabled and a snapshot is loaded, `_cachedVisible*` arrays contain the snapshot's full set. Mixing live plan-state logic with snapshot data causes empty-map regressions.

### Clash state is a no-op in revision mode
`ClashStateService.setClashes` silently skips while `revisionMode.enabled` is true. Live clash data must not overwrite historical snapshot clashes.

## General

### WebSocket presence vs database presence
User may be present in WebSocket room but not reflected in database presence table if Redis is down and fallback event buffer overflows.
→ Do not rely solely on presence table for safety-critical checks.
