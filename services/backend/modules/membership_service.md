---
service: backend
summary: "Pending site membership approval and rejection with broadcast"
paths:
  - backend/app/services/membership_service.py
  - backend/app/api/routes/memberships.py
flows: []
touches:
  - infra/data-stores
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Transition pending site memberships to verified or delete them,
with config broadcast so clients see membership state changes in real time.

## Interface
- `services/membership_service.py::MembershipService(session)`
- `services/membership_service.py::MembershipService.approve(user, membership)` → PendingMemberRead
- `services/membership_service.py::MembershipService.reject(user, membership)` → None
- `api/routes/memberships.py::list_pending_members(site_id, user, session)` → list[PendingMemberRead]
- `api/routes/memberships.py::approve_member(membership_id, user, session)` → PendingMemberRead
- `api/routes/memberships.py::reject_member(membership_id, user, session)` → Response

## State
None.

## Internals
- `approve` sets `verified=True`, `verified_by`, and `verified_at` on `SiteMembership`
- `reject` deletes the `SiteMembership` row entirely
- Both operations emit config broadcast events: `membership.updated` (with `verified: True`) on approve, `membership.deleted` on reject
- `approve` performs extra DB lookups for `User` and `Contractor` to build the `PendingMemberRead` projection
- Routes enforce `Permission.invite_manage` and guard against double-approve or rejecting an already-verified membership

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | SQLModel on SiteMembership, User, Contractor | Persistence and projection lookups |
| modules/core_rbac.md | `require_site_permission` with `Permission.invite_manage` | Authorization gate |

## Gotchas
- Rejecting a verified membership is blocked at the route level; removal must use a different mechanism
- Approve broadcasts `updated`, not `created` — the membership row was already inserted by the invite acceptance flow
- `PendingMemberRead` projection requires extra queries; N+1 risk if bulk-approved without care
