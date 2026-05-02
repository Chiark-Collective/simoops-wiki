---
trigger: { channel: http, ref: "POST /api/planning-cycles/ | /api/planning-cycles/{id}/actualize | /api/planning-cycles/{id}/archive" }
services: [backend]
contracts: []
external: []
---

## Trigger

HTTP POST to create, actualize, or archive a planning cycle.

## Steps

1. Route validates Bearer token and site permission via `core_rbac`
2. **Create**: `CycleService.create_cycle` validates window overlap, inserts row
3. **Adopt baselines**: `import_on_cycle_open` re-tags intersecting site entities as `plan_state='planned'`
4. **Re-import** (optional): `ImportBaselineService.import_baseline` pulls new entities into the cycle
5. **Contractors edit**: Entities are created/modified/tombstoned within the cycle
6. **Submit**: `SubmissionService.submit_plan` captures contractor snapshot
7. **Compare** (review): `CompareService.compare` diffs current rows vs snapshots for divergence
8. **Approve**: `SubmissionService.approve_submission` or `approve_all_submitted`
9. **Actualize**: `ActualizeService.actualize` flips live planned rows to `actual`, deletes tombstoned rows, sets cycle to `live`
10. **Broadcast**: `ws_manager.broadcast_to_room` sends `planning_actualized` event
11. **Clash invalidate**: `invalidate_clash_cache` triggers recomputation
12. **Archive** (later): `CycleService.transition_status` to `archived` (only valid transition from live)

## Side effects

- PostGIS INSERT/UPDATE/DELETE of entity rows and `PlanningCycle` status
- Audit trail entries for every state change
- WebSocket events to `site:{site_id}` room
- Redis pub/sub relay for cross-process broadcast
- Debounced clash cache recomputation

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| Overlapping cycle window | `CycleService.create_cycle` query | 409 Conflict |
| Actualize with empty cycle | `any_planned_rows` check | 422 with detail |
| Actualize non-planning cycle | status guard | 422 Unprocessable |
| Concurrent import/actualize | `pg_advisory_xact_lock` | Serialised by PostgreSQL advisory lock |
| Unauthorized transition | `_VALID_TRANSITIONS` check | 422 Unprocessable |
