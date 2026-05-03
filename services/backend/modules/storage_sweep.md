---
service: backend
summary: "Background sweep retrying failed S3 deletes with backoff"
paths: [backend/app/services/storage_sweep.py]
flows: []
touches: [infra/data-stores]
external: []
last_verified_commit: f9606469ce367229c5c91e03c3ba917779015030
---

## Purpose

Background task that periodically retries S3 deletions which failed during
user-facing requests. Pulls from `pending_storage_deletes` and applies
exponential backoff per row to avoid hammering a transiently-unavailable
MinIO backend.

## Interface

- `storage_sweep.py::sweep_pending_deletes_loop()` → None — supervisor loop started in `app.main.lifespan`, cancelled on shutdown
- `storage_sweep.py::sweep_pending_deletes_once(session)` → int — rows successfully deleted in one batch
- `storage_sweep.py::_retry_one(row, session)` → bool — True if S3 delete succeeded and row should be removed
- `storage_sweep.py::_backoff_for_attempt(attempt_count)` → timedelta

## State

None at module level. Runtime state is the supervisor `asyncio.Task` reference
held by `app.main.lifespan`.

## Internals

- Loop cadence: 60 s (`SWEEP_INTERVAL_SECONDS`)
- Batch size: 100 due rows per iteration (`SWEEP_BATCH_SIZE`)
- Ordering: `last_attempt_at NULLS FIRST, enqueued_at ASC` via DB index
- Backoff: `60 * 2^min(attempt_count, 12)` capped at 24 h (`MAX_BACKOFF_SECONDS`)
- On success: row deleted from table; on failure: `attempt_count`, `last_attempt_at`, `last_error` updated
- Catches `storage.StorageError` (not botocore directly) and re-queues
- Supervisor task survives any iteration failure except `CancelledError`

## Touches

| resource | how | why |
|---|---|---|
| infra/data-stores | `storage.delete_file` offloaded to thread | Retry orphaned S3 objects |
| postgis | Reads/writes `pending_storage_deletes` rows | Queue and bookkeeping |

## Gotchas

- Missing session in `delete_file_no_error` leaves orphans with no retry path
- Backoff cap at 24 h means permanently-broken keys retry once per day
- Loop runs independently of request lifecycle; DB hiccups are logged but don't crash the supervisor
- Health probe flags backlog ≥ 1000 as degraded (`pending_storage_deletes` component → 503)
