---
service: backend
summary: "SmartGroup CRUD with audience-scoped broadcast and sharing toggle"
paths:
  - backend/app/services/smart_group_service.py
  - backend/app/api/routes/smart_groups.py
flows: []
touches:
  - infra/data-stores
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Persist logical entity groupings with query definitions, enforce
owner-or-shared visibility, and handle sharing-toggle side effects via
targeted broadcast audiences.

## Interface
- `services/smart_group_service.py::SmartGroupService(session)`
- `services/smart_group_service.py::SmartGroupService.create_group(user, payload)` → SmartGroup
- `services/smart_group_service.py::SmartGroupService.update_group(user, group, payload)` → SmartGroup
- `services/smart_group_service.py::SmartGroupService.delete_group(user, group)` → None
- `api/routes/smart_groups.py::list_smart_groups(site_id, session, user)` → list[SmartGroupRead]
- `api/routes/smart_groups.py::create_smart_group(payload, session, user)` → SmartGroupRead
- `api/routes/smart_groups.py::get_smart_group(group_id, session, user)` → SmartGroupRead
- `api/routes/smart_groups.py::update_smart_group(group_id, payload, session, user)` → SmartGroupRead
- `api/routes/smart_groups.py::delete_smart_group(group_id, session, user)` → None
- `api/routes/smart_groups.py::evaluate_smart_group(group_id, site_id, session, user, query_start, query_end)` → SmartGroupEvaluationResult
- `api/routes/smart_groups.py::evaluate_adhoc_query(payload, session, user)` → SmartGroupEvaluationResult

## State
None.

## Internals
- Ownership policy enforced by route helpers, not site-permission RBAC: owner can write; owner or shared can read
- `_audience_for` returns `{"type": "owner_or_shared", "owner_id": ..., "is_shared": ...}` for broadcast targeting
- Unsharing (`is_shared` true→false) emits a synthetic `deleted` event to a `non_owner` audience so other clients drop the row
- Resharing (`is_shared` false→true) relies on the frontend treating the owner's `updated` event as a create
- Audit records on create/update/delete via `entity_broadcast_audit::AuditService`
- List endpoint orders by `is_pinned.desc(), name`
- Query evaluation endpoints are stubs returning empty match sets

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | SQLModel on SmartGroup | Persistence and visibility queries |
| modules/entity_broadcast_audit.md | `AuditService`, `snapshot_entity`, `compute_changes` | Audit trail and diff computation |

## Gotchas
- SmartGroups bypass `require_site_permission`; ownership checks live in `_resolve_visible` and `_resolve_owned` helpers
- Unsharing emits `deleted` to non-owners **before** the owner-targeted `updated`; order matters for client consistency
- `evaluate_smart_group` and `evaluate_adhoc_query` are unimplemented stubs
- Query definition is stored as raw JSON with no server-side DSL validation
