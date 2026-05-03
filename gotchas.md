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
→ Allocate ≥2 GB in production. (`db7e54e0` caps JVM heap at 768m and bumps container mem_limit to 1500m.)

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
`~` Resolved by `4d32208c`. `get_site_contractor_filter` and `get_entity_visibility_filter` now return a discriminated union `EntityFilter = AdminFilter | NoAccess | ContractorFilter`. `NoAccess` produces `WHERE FALSE`, so ungated callers can no longer leak rows.

### WebSocket stale permission caches
Cached `site_role`, `site_contractor_id`, and `can_view_others` on `WebSocketConnection` are set at subscribe time and NEVER auto-refreshed.
→ Any DB mutation that changes these MUST call `invalidate_subscription_context` or `invalidate_user_context`.

### Membership delete ordering
When removing a `SiteMembership`, call `invalidate_user_context` **before** deleting the row.
→ If you delete first, `_filter_event_for_user` will deny the `context_invalidated` event because the membership is gone.
→ **Latent bug:** `membership_service.py::MembershipService.reject` at line 80 deletes the membership with no preceding invalidate. Verified as a real permission-correctness issue.

### WebSocket ephemeral events are local-only
`broadcast_ephemeral` does NOT publish to Redis pub/sub.
→ In multi-process deployments, ephemeral drag/resize events only reach subscribers on the same worker.

### Unknown audience types fail closed
`_audience_admits` returns `False` for unrecognised `AudienceType` values.
→ Adding a new audience type without updating the handler silently drops all events using it.
→ Partially mitigated by `54ad568f`: exhaustiveness contract test enumerates `get_args(AudienceType)` and asserts each value has a handler.

### Redis pub/sub no auto-reconnect
`~` Resolved by `65f45a6a`. `_listen` is now a supervisor with reconnect-backoff (1s→60s, exponential, capped). Backoff resets if the inner loop processed at least one message before crashing. `is_healthy` distinguishes "running and connected" from "listener still alive".

### Redis publish silently drops
`~` Partially resolved by `65f45a6a`. `publish` now increments `_dropped_count` and warns on a logarithmic schedule (1, 2, 4, 8, …). Messages are still lost when `_redis is None`; there is no requeue.

### Redis event log clear() unguarded
`~` Resolved by `b8ea3ec5` + `65f45a6a`. `clear()` raises when `environment != "test"`. Key prefixes are now env-scoped (`simoops:{env}:events:`), so a misfired test command cannot nuke production.

### Data lock timezone stripping
`~` Resolved by `ad72fbf4`. `_to_aware_utc` converts aware inputs to UTC via `astimezone` and tags naive inputs as UTC. `replace(tzinfo=None)` is no longer used.

### Entity broadcast used by planning for clash invalidation
`~` Resolved by `30128e01`. `invalidate_clash_cache` moved to `services/clash/clash_cache.py`. Direct callers import from there; the tight coupling between entity broadcast and planning is eliminated.

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
`~` Resolved by `8738a273`. `ContextProvider` Protocol now declares `requires` and `provides` ClassVar tuples. `registry.py` builds run order via `graphlib.TopologicalSorter` and raises on duplicate key, missing producer, or cycle.

### Weather cache short TTL
`weather/cache.py` caches Open-Meteo responses with a short TTL (15m current / 1h forecast / 5m timeline).
→ Repeated report exports within the same hour re-fetch weather.
→ Left as-is (`f36da393`); rationale comments at the constants explain Open-Meteo is the free/unkeyed tier and rate-limits per-IP, so global TTL is the right level.

### Presence heartbeat required
`presence_manager.py` drops users whose heartbeat expires.
→ Clients that stop sending `presence_heartbeat` will disappear from the presence list even if the WebSocket is still connected.

### Pre-migration audit entries cannot be reverted
`AuditRevertService` raises HTTP 400 when the target `AuditLog.snapshot` is `None`.
→ Any audit row written before the snapshot column was backfilled is non-revertible.

### Audit-revert geometry SRID fallback
`~` Resolved by `9d6ac591`. `_deserialize_field_value` now raises on missing SRID instead of silently defaulting to `3857`.

### Text label delete bypasses broadcast helper
`~` Resolved by `c89b84c2`. `delete_text_label` now routes through `_broadcast_event` instead of calling `ws_manager.broadcast_entity_event` directly.

### JWKS stale cache on prolonged outage
`~` Resolved by `07feff64`. `get_jwks_cache_age_seconds()` and `is_jwks_serving_stale()` surface cache age. `/health/ready` reports `jwks` component and flips to 503 when age > 2×TTL (10 min) or serving stale. Warns on fresh→stale transition, INFO on recovery.

### JWKS relaxed issuer boundary
`~` Resolved by `963a5d54`. `SIMOOPS_KEYCLOAK_VERIFY_ISSUER` env knob (default `False`) allows operators to enable issuer verification without a code change once the canonical Keycloak origin is stable.

### Storage health transient false negatives
`~` Resolved by `07feff64`. `check_health` now returns `Literal["ok", "unreachable", "misconfigured"]`. Permanent `ClientError` codes (`NoSuchBucket`, `AccessDenied`, etc.) are classified as misconfigured; the rest stay unreachable.

### Storage silent delete failures
`~` Resolved by `47cd368e` + `0fc7f189`. `delete_file_no_error` is now async and inserts a `PendingStorageDelete` row on failure. `storage_sweep.py` retries every 60s with exponential backoff capped at 24h.

### Storage delete retry queue backlog
`pending_storage_deletes` backlog ≥ 1000 flips `/health/ready` to 503.
→ Operators should monitor the `pending_storage_deletes` component to catch runaway accumulation before storage costs spike.

### TIMESTAMPTZ migration for feature_versions
Migration `096` alters `feature_versions.start_at` / `end_at` from `TIMESTAMP` to `TIMESTAMPTZ`. Pre-migration, writes silently stripped timezone offsets; reads serialised naive datetimes that the frontend parsed as runner-local, causing `isEntityActiveAt` to reject features in revision mode on non-UTC runners.

## Frontend

### Zone.js + MapLibre symbol-layer corruption
GeoJSON sources that start empty and are later populated via `setData` silently fail for symbol layers.
→ `~` Mitigated by `bfcbcb21`/`62e111d3`: `RecreatableMapSource` owns the recreate-on-first-populate dance and replays filter/layout/paint/feature-state across recreations. The underlying MapLibre/Zone.js bug still exists; new symbol-layer sources should use `RecreatableMapSource`.

### MapLibre handlers fire outside Angular zone
`ngZone.runOutsideAngular` during map construction is required for 60fps performance, but all pointer/drag/hover handlers fire outside the zone.
→ `~` Mitigated by `bfcbcb21`: `mapEventSignal<T>` bridges MapLibre events into Angular signals, bypassing `markForCheck` races.

### AuthService test token read once at construction
`window.__SIMOOPS_TEST_TOKEN__` is read in the `AuthService` constructor. Injecting it after bootstrap has no effect.
→ Set the token before `bootstrapApplication` resolves.

### UserService removes pending invite before API resolves
`~` Resolved by `99327921`. `fetchCurrentUser` defers `localStorage.removeItem` for `simoops_pending_invite_token` until `acceptInviteLink` resolves. `catchError` leaves both keys in place so the next `/me` retries the acceptance.

### Dashboard wiring subscriptions are app-scoped
`~` Resolved by `6871ba37`. `DashboardBootstrapWiringService` and `DashboardInteractionWiringService` now use component-scoped providers on `DashboardComponent`. `DestroyRef` is the dashboard's, so subscriptions unsubscribe automatically when the dashboard is destroyed.

### PanelStateService silently swallows parse failures
`~` Resolved by `b7c3b270`. `JSON.parse` failures now warn via `createLogger('PanelState')` with truncated raw value. Per-field validation drops also emit warnings.

### WebSocket catch-up dedup races with live events
`pendingCatchUpSnapshot` is frozen at `sendCatchUp` time. If a live broadcast arrives after send but before the response with `seq > snapshot`, the snapshot threshold prevents silent dropping of legitimately missed events. See `websocket.service.ts::sendCatchUp` "C2 regression" comment.

### Offline queue optimistic state may drift
`~` Partially resolved by `33216699`. `executeMutation` now suppresses WS delta application during in-flight mutations and rolls back on 500. If the API succeeds but the WS broadcast is delayed, local state may still be temporarily out of sync with the server seq.

### Map source recreation resets filters and layout properties
`~` Resolved by `bfcbcb21`. `RecreatableMapSource` records `setFilter` / `setFeatureState` / `setLayoutProperty` / `setPaintProperty` in a typed replay log and replays them on recreation. Callers no longer need to re-apply state manually.

### SiteContextService getters return new Observable references
`~` Resolved by `ebfa43aa`. `selectedShift$` and `selectedDate$` are now `readonly` fields, not getters. The synchronous `selectedShift`/`selectedDate` getters remain for fresh reads.

### Sync bindings must be injected eagerly
`ContractorSyncBinding`, `ShiftSyncBinding`, `InviteSyncBinding`, and others must be injected before the first WS broadcast arrives. Lazy injection (e.g., behind `*ngIf`) misses early events.
→ `~` Mitigated by `4bdd36cb`: all nine bindings now carry explicit "Materialised once at app start" comments forbidding lazy injection.

### EntityStore optimistic updates only for tokens and plants
`~` Partially resolved by `4539e12d` + `6c05ffe2`. `SyncCoordinator<T>` now provides optimistic snapshot, 409 rollback, and WS dedup uniformly across tokens, plants, areas, deliveries, POIs, text-labels, and alerts. The design-flag cluster G7 remains open for a full `EntitySyncEngine` abstraction.

### Revision mode bypasses plan-state filter
`~` Resolved by `dbcb7815`. `ViewModeService.shouldBypassPlanFilter$` gates the bypass for all read-only modes (revision + viewing_submitted + compare). Inconsistent combined states are now unrepresentable.

### Clash state is a no-op in revision mode
`~` Resolved by `dbcb7815`. `ViewModeService.shouldDropLiveEvents$` gates clash drops for all read-only modes. `ClashStateService.setClashes` now warns via the service logger on each drop instead of going silent.

### ViewModeService setAppMode no-op during revision
`setAppMode` is a silent no-op while revision is active.
→ Callers that need to re-apply a mode after exiting revision must trigger the transition separately. The cycle-driven default logic does this automatically.

### RecreatableMapSource replay log growth
`RecreatableMapSource` accumulates every `setFilter` / `setFeatureState` / `setLayoutProperty` / `setPaintProperty` call in its replay log.
→ High-frequency dynamic updates (e.g., per-frame hover effects) can cause unbounded log growth. Use `removeFeatureState` to clear entries that should not replay.

## General

### WebSocket presence vs database presence
User may be present in WebSocket room but not reflected in database presence table if Redis is down and fallback event buffer overflows.
→ Do not rely solely on presence table for safety-critical checks.

