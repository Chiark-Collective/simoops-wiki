---
service: ui
summary: Generic helper for optimistic entity sync, rollback, and WS dedup.
paths:
  - services/sync-coordinator.ts
  - services/sync-coordinator.spec.ts
flows: []
touches: []
external: []
last_verified_commit: f9606469ce367229c5c91e03c3ba917779015030
---

## Purpose
Per-entity-kind sync helper that owns optimistic snapshots, pending-set suppression, tombstones, and the mutate envelope (success / 409 / non-409 paths). Composed inside domain services (`EntityService`, `DeliveryService`, `PoiService`, `TextLabelService`, `AlertService`) to replace ad-hoc per-type optimistic logic.

## Interface
- `services/sync-coordinator.ts::SyncCoordinator<T>` — Generic class parameterized by an entity with `{ id: string }`. Constructor takes an `EntityStore<T>` and `SyncCoordinatorOpts` (`entityType` string).
- `services/sync-coordinator.ts::ConflictDetail` — Structured 409 conflict description: `entityType`, `entityId`, `message`, `currentData`, `conflictingFields`, `clientValues`.
- `beginOptimistic(id, mutator)` — Snapshot current store value, apply mutator optimistically, mark id pending.
- `beginOptimisticPatch(id, patch)` — Sugar over `beginOptimistic` for partial-field patches.
- `isPending(id)` / `pendingIds()` — Query pending state. `pendingIds` returns a live `ReadonlySet<string>`.
- `beginInFlight(id)` — Snapshot without optimistic apply. Used by `OfflineQueueService` replay: state was already applied at enqueue time, only WS suppression + rollback snapshot needed.
- `clearInFlight(id, applyEntity?)` — Clear pending mark and snapshot; optionally write the server entity.
- `rollbackInFlight(id)` — Restore pre-flight snapshot and clear pending. Used on non-409 replay failure.
- `mutate(id, apiCall, onConflict)` — Wrap an `Observable<T>` API call with the full envelope: success clears pending and applies server entity; 409 parses conflict, patches server state, calls `onConflict`, re-throws; non-409 rolls back to snapshot and re-throws.
- `shouldApplyWsUpdate(id)` — False while pending or tombstoned.
- `filterBatchUpdates(updates)` — Strip pending and tombstoned ids from a `Map<string, U>` in place.
- `recordTombstone(id)` / `reviveTombstone(id)` / `isTombstoned(id)` — Tombstone lifecycle.
- `filterRevived(items)` — Drop tombstoned items from a fresh list (e.g., HTTP snapshot).
- `reset()` — Clear all internal state (pending, snapshots, tombstones).

## State
- `_pending: Set<string>` — ids with an optimistic mutation or in-flight API call. WS broadcasts for these ids are suppressed.
- `_snapshots: Map<string, T>` — pre-mutation store values for rollback on non-409 failure.
- `_tombstones: Set<string>` — ids explicitly deleted by the local user. Prevents stale HTTP snapshots and late WS broadcasts from reintroducing the entity.

Invariants:
- `_pending.has(id) === true` ⟂ WS update for `id` is applied to the store.
- `_tombstones.has(id) === true` ⟂ HTTP snapshot list and WS batch updates for `id` are filtered out.
- `beginOptimistic` on a missing store id still marks pending (no snapshot taken) so a concurrent WS broadcast is suppressed.
- `mutate` expects the caller to have already invoked `beginOptimistic` (or `beginInFlight`) so a snapshot exists for rollback.

## Internals
- `mutate` uses `tap` for the success path and `catchError` for failure paths. On 409 it deletes the pending mark but not the snapshot until after `onConflict` is invoked, then patches `currentData` into the store or re-emits the full items array if `currentData` is absent.
- `_parse409` drills into `err.error.error.detail` and falls back to a generic message when the detail shape is unexpected.
- `beginInFlight` / `clearInFlight` / `rollbackInFlight` form the offline-queue replay pair. The queue applied the mutation optimistically at enqueue time; replay only needs to prevent WS races and provide a rollback target on 500.
- Instantiated per entity kind in `EntityService` (`tokenSync`, `plantSync`, `areaSync`) and in delivery/POI/text-label/alert services with equivalent patterns.
- No Angular DI dependency; services instantiate their own coordinator and call `reset()` on site switch.

## Gotchas
- `mutate` re-throws on both 409 and non-409 failure. Callers must `.catchError` if they want to swallow the error.
- On 409 without `currentData`, the coordinator re-emits the full store array so subscribers refresh against the rolled-back state. This produces an extra emission.
- `filterBatchUpdates` mutates the input map in place and returns it. Do not rely on the original reference remaining unmodified.
- Tombstones are not persisted across page reloads. A deleted entity can reappear after refresh if the server still has it.
- `pendingIds()` returns a live view of the internal Set. Callers must treat it as read-only.
