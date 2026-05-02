---
service: backend
summary: "Entity broadcast, clash cache invalidation, and audit trail subsystem"
paths:
  - backend/app/services/entity/entity_broadcast.py
  - backend/app/services/entity/entity_audit.py
  - backend/app/services/entity/audit_service.py
  - backend/app/services/entity/audit_revert_service.py
  - backend/app/services/entity/audit_snapshot_reconstructor.py
  - backend/app/services/entity/audit_timeline_service.py
  - backend/app/core/entity_audit_types.py
flows:
  - services/backend/flows/entity_creation.md
  - services/backend/flows/entity_update.md
touches: []
external: []
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Decoupled broadcast and audit functions for entity mutations. Broadcast helpers
emit WebSocket events and schedule clash recomputation without inheriting from
`EntityServiceBase`. Audit services record field-level diffs, support revision
mode reconstruction, revert-to-snapshot, and timeline enumeration.

## Interface
- `entity_broadcast.py::invalidate_clash_cache(site_id)` → None
- `entity_broadcast.py::invalidate_and_broadcast(site_id, event_type, entity_type, entity_id, data, delta)` → int
- `entity_broadcast.py::broadcast_entity_event(entity, entity_type, event_type, response, delta)` → int
- `entity_broadcast.py::broadcast_update_delta(entity, entity_type, payload, response, field_groups)` → None
- `entity_audit.py::record_modified_fields(entity, payload, field_groups)` → None
- `entity_audit.py::stamp_audit_fields(entity, user, membership)` → None
- `entity_audit.py::record_update_audit(entity, entity_type, entity_label, user, membership, pre_snapshot, audit_service)` → None
- `audit_service.py::snapshot_entity(entity, exclude)` → dict
- `audit_service.py::snapshot_entity_for_storage(entity, exclude)` → dict
- `audit_service.py::compute_changes(old_snapshot, new_snapshot)` → dict
- `audit_service.py::compute_revision_hash(snapshot)` → str
- `audit_service.py::AuditService.record(...)` → AuditLog
- `audit_service.py::AuditService.record_batch(entries, actor, membership)` → list[AuditLog]
- `audit_revert_service.py::AuditRevertService.revert_to_entry(entry_id, actor, membership)` → AuditLog
- `audit_snapshot_reconstructor.py::AuditSnapshotReconstructor.reconstruct(site_id, at_time, entity_types)` → list[AuditLog]
- `audit_snapshot_reconstructor.py::AuditSnapshotReconstructor.summarize(site_id, at_time, entity_types)` → SnapshotRevisionSummary
- `audit_timeline_service.py::AuditTimelineService.list_timeline(site_id, since, until, entity_types, order, limit)` → RevisionTimelineResponse
- `core/entity_audit_types.py::is_recognised_audit_entity_type(value)` → bool

## Internals
- `snapshot_entity` serialises geometry as human-readable summaries for diffs
- `snapshot_entity_for_storage` serialises geometry as GeoJSON for round-tripping
- `compute_changes` flattens `extra` and `properties` sub-keys into top-level entries
- `record_modified_fields` normalises raw payload fields to semantic groups for OCC
- `broadcast_update_delta` excludes `EXCLUDED_FROM_CONFLICT` fields and normalises to semantic field names
- `invalidate_clash_cache` delegates to `clash_cache.schedule_recomputation` to coalesce rapid mutations
- `AuditRevertService` deserialises UUID, datetime, and geometry fields when applying snapshots
- `AuditSnapshotReconstructor` uses `DISTINCT ON` over `(entity_type, entity_id)` with reverse-timestamp ordering; tombstones and null snapshots are filtered in Python
- `AuditTimelineService` uses `limit + 1` to detect truncation without a COUNT query
- `entity_audit_types.py` defines the canonical `entity_type` strings; `'area'` is magic-expanded to feature types server-side

## Touches
| resource | how | why |
|---|---|---|
| services/backend/modules/websocket_runtime.md | `ws_manager.broadcast_entity_event` | Push events to site subscribers |
| services/backend/modules/redis_core.md | Redis pub/sub via `ws_manager` | Cross-worker broadcast transport |
| services/backend/modules/entity_service.md | Called by CRUD and schedule ops | Audit + broadcast on every mutation |

## Gotchas
- `snapshot_entity` strips `id`, `site_id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `last_modified_fields` — reconstructors must re-inject identity fields
- Audit rows are staged in the same transaction as entity writes; partial commits cannot leave a changed entity without audit (H3)
- `AuditSnapshotReconstructor` filters tombstones post-DISTINCT-ON; moving `action != deleted` into WHERE would falsely resurrect deleted entities
- `snapshot IS NOT NULL` cannot be expressed in the SQLModel WHERE clause against JSONB; null-snapshot filtering also happens in Python
- Reverting to a pre-migration snapshot (no `snapshot` field) raises 400
- `entity_broadcast.py::invalidate_clash_cache` is imported by planning services; keep it free of entity-service inheritance requirements
