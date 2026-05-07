---
service: backend
summary: "Site-scoped RBAC: permissions, roles, and membership resolution"
paths: [backend/app/core/permissions.py, backend/app/core/rbac.py]
flows: []
touches: [infra/data-stores]
external: []
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose
Define all grantable operations and resolve whether a user may perform an
action on a specific site via their `SiteMembership`.

## Interface
- `core/permissions.py::Permission` — Enum of all grantable operations (`entity.create`, `data.lock`, etc.)
- `core/permissions.py::ROLE_PERMISSIONS` — `dict[SiteRole, frozenset[Permission]]`
- `core/permissions.py::ROLE_RANK` — `dict[SiteRole, int]`; higher = more privileged
- `core/permissions.py::Permission.site_settings_basic` — "site.settings.basic" (coordinator-grade)
- `core/permissions.py::role_has_permission(role, permission)` → bool
- `core/permissions.py::can_assign_role(inviter_role, target_role)` → bool
- `core/rbac.py::get_site_membership(user, site_id, session)` → SiteMembership | None
- `core/rbac.py::has_site_permission(user, site_id, permission, session)` → bool
- `core/rbac.py::require_site_permission(user, site_id, permission, session)` → SiteMembership
- `core/rbac.py::require_site_or_global_permission(user, site_id, permission, session, global_resource_label)` → SiteMembership | None
- `core/rbac.py::EntityFilter` — `AdminFilter | NoAccess | ContractorFilter`
- `core/rbac.py::AdminFilter` — dataclass; user sees all entities
- `core/rbac.py::NoAccess` — dataclass; produces `WHERE FALSE`
- `core/rbac.py::ContractorFilter` — dataclass; scoped to `contractor_id`
- `core/rbac.py::get_site_contractor_filter(user, site_id, session)` → EntityFilter
- `core/rbac.py::get_entity_visibility_filter(user, site_id, entity_type, session)` → EntityFilter
- `core/rbac.py::apply_entity_filter(stmt, filt, contractor_col, *, allow_null)` → Select[_T]

## State
Immutable module-level mappings loaded at import time.

| symbol | type | semantics |
|---|---|---|
| `ROLE_PERMISSIONS` | `dict[SiteRole, frozenset[Permission]]` | Frozen role → permission set |
| `ROLE_RANK` | `dict[SiteRole, int]` | viewer/client=0, member=1, coordinator=2, admin=3 |

Invariants:
- Permission sets are cumulative by rank: viewer == client < member < coordinator < admin
- `ROLE_PERMISSIONS` and `ROLE_RANK` must remain synchronized with `SiteRole` enum
- Superadmins bypass all checks regardless of `SiteMembership` existence or verification state
- `site_settings_basic` added to `_COORDINATOR_PERMISSIONS`; guards site fields editable from Settings → Site tab (cross-contractor visibility, elevation grace, etc.)
- Contractor scope enforced on entity creation: members may only create entities tagged with their own `contractor_id`

## Internals
- `get_site_membership` filters on `verified == True`; unverified memberships are invisible to RBAC
- `require_site_permission` returns a synthetic `SiteMembership(role=admin, verified=True)` for superadmins without an explicit membership
- Synthetic memberships lack a `contractor_id`; downstream code that expects one may misbehave
- `client` role shares the same permission set as `viewer` but receives `AdminFilter` from contractor filters (sees all contractors' entities)
- `require_site_or_global_permission` treats `site_id=None` as superadmin-only; no membership is returned for global resources
- `get_entity_visibility_filter` uses OR-logic: membership-level `can_view_others_*` flag OR site-level `member_can_view_others_*` flag grants cross-contractor visibility
- `apply_entity_filter` renders `AdminFilter` unchanged, `NoAccess` as `WHERE FALSE`, and `ContractorFilter` as equality (or equality-OR-NULL with `allow_null=True` for plants)
- Only `"workers"`, `"plant"`, `"zones"` are recognized entity types; any other string falls through to the membership's `contractor_id` filter
- `has_site_permission` returns `False` both for missing membership and for insufficient role permissions (indistinguishable)

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | SQLModel select on `SiteMembership`, `Site`, `User` | Resolve membership, role, and visibility flags |

## Gotchas
- **RESOLVED** — The old silent-filtering ambiguity (`None` meant both "no filter needed" and "deny everything") is eliminated by the `EntityFilter` discriminated union; `NoAccess` produces `WHERE FALSE` and is distinct from `AdminFilter`
- When removing a `SiteMembership`, call `websocket_runtime::invalidate_user_context` **before** delete so the `context_invalidated` event can still be delivered
- `site_settings` permission remains admin-only (planning toggles); `site_settings_basic` is coordinator+ (non-planning site fields)
