---
service: backend
summary: "Contractor submissions, dedup, snapshots, and insights"
paths: [
  backend/app/services/planning/submission_service.py,
  backend/app/services/planning/submission_insight_service.py,
  backend/app/services/planning/submission_snapshot_service.py,
  backend/app/services/planning/submission_dedup.py,
  backend/app/services/planning/submission_snapshots.py,
  backend/app/services/planning/submission_snapshot_store.py,
]
flows: [planning_submission_flow]
touches: [postgis]
external: []
last_verified_commit: TBD
---

## Purpose

Manages contractor plan submissions within a planning cycle, captures immutable
snapshots of submitted entity state, and surfaces per-contractor insight
dashboards with pending-change detection.

## Interface

- `SubmissionService(session).create_submission(cycle_id, contractor_id)` → `ContractorSubmission`
- `SubmissionService(session).bulk_create_submissions(cycle_id, contractor_ids)` → list
- `SubmissionService(session).submit_plan(cycle_id, contractor_id, user_id)` → `ContractorSubmission`
- `SubmissionService(session).approve_submission(cycle_id, contractor_id, user_id)` → `ContractorSubmission`
- `SubmissionService(session).approve_all_submitted(cycle_id, user_id)` → int
- `SubmissionService(session).submit_all_pending(cycle_id, user_id)` → int
- `SubmissionService(session).request_revision(cycle_id, contractor_id, note)` → `ContractorSubmission`
- `SubmissionInsightService(session).list_submission_insights(cycle_id)` → list
- `SubmissionInsightService(session).get_submission_insight_detail(cycle_id, contractor_id)` → detail
- `SubmissionInsightService(session).list_pending_summaries(cycle_id)` → list
- `SubmissionSnapshotService(session).sync_contractor_plan(cycle_id, contractor_id, user_id)` → snapshot result
- `backend/app/services/planning/submission_snapshot_store.py::capture_submission_snapshot(session, submission, entities)` → items
- `backend/app/services/planning/submission_snapshot_store.py::get_submission_snapshot(session, submission_id)` → `{entity_type: {entity_id: snapshot_data}}`

## State

Runtime state is minimal; snapshots are persisted.

| State | Location | Lifecycle |
|---|---|---|
| `ContractorSubmission` rows | postgis | Persistent |
| `ContractorSubmissionSnapshotItem` rows | postgis | Persistent; replaced on re-submit |

## Internals

- `_VALID_TRANSITIONS` in `submission_service.py`: draft→submitted→approved or revision_requested→submitted
- `submit_plan` calls `SubmissionSnapshotService.sync_contractor_plan` before transitioning status
- `sync_contractor_plan` locks the cycle with `pg_advisory_xact_lock`, loads contractor-scoped planned rows, and calls `capture_submission_snapshot`
- `capture_submission_snapshot` deletes prior items for the submission then inserts fresh rows
- `submission_snapshot_store.py` maps model class names to entity type tags (`Worker` → `"worker"`, etc.)
- `submission_snapshots.py` provides duck-typed dataclasses (`_SnapshotToken`, `_SnapshotPlant`, etc.) for read-path reconstruction
- `submission_dedup.py` collapses recurring occurrences by `schedule_group_id`, falling back to `(contractor_id, label|name|description)`
- `SubmissionInsightService` overlays live `tombstoned_at` onto snapshot rows for "Marked for Removal" sections
- `backend/app/services/planning/submission_dedup.py::_pending_after_submission` computes live rows whose dedup identity is absent from the submitted set
- `backend/app/services/planning/pending_row_differ.py::is_newer_than` normalizes naive timestamps to UTC before comparison

## Touches

| resource | how | why |
|---|---|---|
| postgis | SQLModel CRUD | Submissions, snapshot items, entity baselines |
| [websocket_runtime](websocket_runtime.md) | `ws_manager.broadcast_to_room` | Submission status updates |
| [clash_engine](clash_engine.md) | `invalidate_clash_cache` | Recompute clashes on bulk submit |

## Gotchas

- Re-submission after `revision_requested` overwrites the prior snapshot entirely
- `submit_all_pending` snapshots each contractor sequentially under one advisory lock
- Site-wide rows (`contractor_id IS NULL`) are included in snapshots but excluded from per-contractor pending diffs
- Building/zone features are excluded from plan-authored sections via `_NON_PLAN_FEATURE_TYPES`
