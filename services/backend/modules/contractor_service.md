---
service: backend
summary: "Contractor CRUD with audit trail and config broadcast"
paths:
  - backend/app/services/contractor_service.py
  - backend/app/api/routes/contractors.py
flows: []
touches:
  - infra/data-stores
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Orchestrate contractor persistence, audit, and real-time broadcast.
Routes own HTTP shape; the service owns side effects and validation.

## Interface
- `services/contractor_service.py::ContractorService(session)`
- `services/contractor_service.py::ContractorService.create_contractor(user, payload, membership)` → Contractor
- `services/contractor_service.py::ContractorService.update_contractor(user, contractor, payload, membership)` → Contractor
- `services/contractor_service.py::ContractorService.delete_contractor(user, contractor, membership)` → None
- `api/routes/contractors.py::list_contractors_public(site_id, session)` → list[ContractorPublic]
- `api/routes/contractors.py::list_contractors(site_id, session, user)` → list[ContractorRead]
- `api/routes/contractors.py::create_contractor(payload, session, user)` → ContractorRead
- `api/routes/contractors.py::update_contractor(contractor_id, payload, session, user)` → ContractorRead
- `api/routes/contractors.py::delete_contractor(contractor_id, session, user)` → None

## State
None.

## Internals
- Duplicate name checked per-site; raises `ValueError("duplicate_name")`
- Delete scans Worker, Plant, and GeometadataFeature for dependencies; raises `ValueError(f"has_assigned_{label}")` for the first kind found
- Audit records created via `entity_broadcast_audit::AuditService` for create/update/delete
- Config broadcast (`contractor.created/updated/deleted`) emitted after every mutating operation
- Routes translate `ValueError` to 400 HTTPException
- Contractor colors are generated client-side from the contractor ID

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | SQLModel on Contractor, Worker, Plant, GeometadataFeature | Persistence and dependency checks |
| modules/entity_broadcast_audit.md | `AuditService`, `snapshot_entity_for_storage`, `compute_changes` | Audit trail and field-level change tracking |
| modules/core_rbac.md | `require_site_permission` with `Permission.contractor_manage` | Authorization gate |

## Gotchas
- Delete only reports the first dependency kind encountered, not a complete list
- `ValueError` strings (`duplicate_name`, `has_assigned_*`) are API contracts between service and route; changing them breaks HTTP error mapping
- No cascade delete; caller must reassign or remove all dependents before delete succeeds
