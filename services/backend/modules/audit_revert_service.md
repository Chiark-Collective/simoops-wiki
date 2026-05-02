---
service: backend
summary: "Reverts entities to previous audit snapshot states"
paths:
  - backend/app/services/entity/audit_revert_service.py
flows: []
touches:
  - services/backend/modules/entity_broadcast_audit.md
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Restores an entity to the state captured in a specific audit log snapshot and
records a new audit entry documenting the revert. Supports all audited entity
types including geometadata features.

## Interface
- `audit_revert_service.py::AuditRevertService.revert_to_entry(entry_id, actor, membership)` → AuditLog

## State
None at module level. All state is persistent (PostGIS).

## Internals
- `_IMMUTABLE_FIELDS` prevents overwriting `id`, `site_id`, `created_by`, `created_at` during reversion
- `_ENTITY_TYPE_TO_MODEL` maps audit `entity_type` strings to SQLModel classes; feature types map to `GeometadataFeature`
- `_resolve_model_class` detects feature types by attempting `FeatureType(entity_type)` instantiation
- `_deserialize_field_value` inspects SQLAlchemy column types to restore UUIDs, ISO datetimes, and GeoJSON geometries as WKBElement
- Geometry deserialization defaults to srid=3857 when the column type has no explicit srid
- The revert audit entry carries `extra.reverted_to_hash` and `extra.reverted_from_entry_id`
- `updated_by` is set to the actor performing the revert

## Touches
| resource | how | why |
|---|---|---|
| services/backend/modules/entity_broadcast_audit.md | `AuditService.record`, `snapshot_entity`, `compute_changes` | Audit staging and diff computation |

## Gotchas
- Pre-migration audit entries with `snapshot=None` raise HTTP 400
- Unknown entity types raise HTTP 400; deleted entities raise HTTP 404
- Immutable fields are skipped silently during snapshot application
- Geometry srid fallback to 3857 may be incorrect for layers using a different projection
