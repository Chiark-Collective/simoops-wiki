---
service: backend
summary: "Shift CRUD with audit and broadcast; no cascade deletion"
paths:
  - backend/app/services/shift_service.py
  - backend/app/api/routes/shifts.py
flows: []
touches:
  - infra/data-stores
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Persist shift definitions for a site, record audit trails, and broadcast
mutations. Shift deletion never cascades to entities.

## Interface
- `services/shift_service.py::ShiftService(session)`
- `services/shift_service.py::ShiftService.create_shift(user, payload, membership)` → Shift
- `services/shift_service.py::ShiftService.delete_shift(user, shift, membership)` → None
- `api/routes/shifts.py::list_shifts(site_id, session, user)` → list[ShiftRead]
- `api/routes/shifts.py::create_shift(payload, session, user)` → ShiftRead
- `api/routes/shifts.py::delete_shift(shift_id, session, user)` → None

## State
None.

## Internals
- Duplicate name checked per-site; raises `ValueError("duplicate_name")`
- No update endpoint or method exposed; to change a shift, delete and recreate
- Delete does not cascade to tokens or plants — entities use explicit `start_at`/`end_at` ranges
- Audit record and config broadcast (`shift.created/deleted`) on every mutation
- List endpoint orders by `created_at, id`
- `Shift.starts_at` and `ends_at` use `TIMESTAMPTZ` so the API serialises with an explicit UTC offset

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | SQLModel on Shift | Persistence and uniqueness checks |
| modules/entity_broadcast_audit.md | `AuditService`, `snapshot_entity_for_storage` | Audit trail on create and delete |
| modules/core_rbac.md | `require_site_permission` with `Permission.shift_manage` | Authorization gate |

## Gotchas
- No shift update operation; mutation requires delete + recreate
- Deleting a shift does not affect entities that reference it via datetime ranges rather than FK
- Overnight shifts (e.g., Back Shift 17:00–01:00) have `ends_at < starts_at`; consumers must handle wraparound
