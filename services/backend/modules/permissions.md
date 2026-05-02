---
service: backend
summary: "Permission enum and role-to-permission mapping for site-scoped RBAC"
paths: [backend/app/core/permissions.py]
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Define every grantable operation in the system and map each `SiteRole` to its
permission set. Provides role-hierarchy utilities for the invite system.

## Interface
- `core/permissions.py::Permission` — `str` enum of all grantable operations
- `core/permissions.py::ROLE_PERMISSIONS` — `dict[SiteRole, frozenset[Permission]]`
- `core/permissions.py::ROLE_RANK` — `dict[SiteRole, int]`; higher = more privileged
- `core/permissions.py::role_has_permission(role, permission)` → `bool`
- `core/permissions.py::can_assign_role(inviter_role, target_role)` → `bool`

## State
Immutable module-level mappings loaded at import time.

| symbol | type | semantics |
|---|---|---|
| `ROLE_PERMISSIONS` | `dict[SiteRole, frozenset[Permission]]` | Frozen role → permission set |
| `ROLE_RANK` | `dict[SiteRole, int]` | viewer/client=0, member=1, coordinator=2, admin=3 |

Invariants:
- Permission sets are cumulative by rank: viewer == client < member < coordinator < admin
- `ROLE_PERMISSIONS` and `ROLE_RANK` must remain synchronized with `SiteRole` enum

## Internals
- `viewer` and `client` share the same permission set
- `client` role is not contractor-scoped; RBAC filters return `None` for them so they see all contractors' entities
- `entity_create`, `entity_edit`, `entity_delete` are "own" scoped (member's contractor only)
- `entity_manage_any` lifts scoping for coordinators and admins
- `can_assign_role` uses `ROLE_RANK` to prevent inviters from assigning roles above their own level
- Superadmins bypass all permission checks in `core/rbac.py`; they do not appear in these mappings

## Touches
None.

## Gotchas
- `role_has_permission` returns `False` for unknown roles; callers should ensure the role exists in `SiteRole`
- `Permission` is a `str` enum so values can be compared directly to strings for serialization
