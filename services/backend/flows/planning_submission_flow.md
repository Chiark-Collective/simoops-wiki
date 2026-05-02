---
trigger: { channel: http, ref: "POST /api/planning-cycles/{id}/submissions/{cid}/submit | /approve | /reject" }
services: [backend]
contracts: []
external: []
---

## Trigger

HTTP POST to submit, approve, or request revision of a contractor's plan within
a planning cycle.

## Steps

1. Route validates Bearer token and site permission via `core_rbac`
2. **Submit**:
   - `SubmissionService.submit_plan` calls `SubmissionSnapshotService.sync_contractor_plan`
   - `sync_contractor_plan` acquires advisory lock, loads contractor-scoped planned rows
   - `capture_submission_snapshot` deletes prior snapshot items, inserts fresh `ContractorSubmissionSnapshotItem` rows
   - `SubmissionService._transition` sets status to `submitted`
3. **Compare** (coordinator review):
   - `CompareService.compare` shows snapshot vs current row divergence
   - `ClashCompareService.compute_clash_diff` evaluates planned vs actual clashes (post-actualize)
4. **Approve**:
   - `SubmissionService.approve_submission` transitions status to `approved`
5. **Reject / Request revision**:
   - `SubmissionService.request_revision` transitions status to `revision_requested`, sets `revision_note`
6. **Bulk operations**:
   - `approve_all_submitted` and `submit_all_pending` iterate submissions in one transaction
7. **Broadcast**: `ws_manager.broadcast_to_room` sends `planning_submission_updated` event
8. **Insight refresh**: `SubmissionInsightService` recomputes pending summaries on next read

## Side effects

- PostGIS INSERT/UPDATE of `ContractorSubmission` and `ContractorSubmissionSnapshotItem`
- Audit entries for status transitions
- WebSocket events to `site:{site_id}`
- Clash cache invalidation on bulk submit

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| Submit without submission row | `sync_contractor_plan` check | 404 Not Found |
| Invalid status transition | `_VALID_TRANSITIONS` check | 422 Unprocessable |
| Snapshot into non-planning cycle | status guard | 422 Unprocessable |
| Duplicate submission create | unique constraint check | 409 Conflict |
| Concurrent submit | `pg_advisory_xact_lock` | Serialised |
