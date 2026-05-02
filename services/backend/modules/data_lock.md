---
service: backend
summary: "Site-level data lock: immutability boundary for historical entities"
paths: [backend/app/core/data_lock.py]
flows: []
touches: []
external: []
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Prevent non-admin users from modifying entities whose `end_at` falls on or
before the site's lock boundary.

## Interface
- `core/data_lock.py::is_entity_locked(entity_end_at, lock_boundary)` → bool
- `core/data_lock.py::is_user_admin_or_superadmin(membership_role, is_superadmin)` → bool
- `core/data_lock.py::require_not_locked(entity_end_at, site, membership_role, is_superadmin, action)` → None

## Internals
- Both datetimes normalized to naive UTC (`replace(tzinfo=None)`) before comparison to prevent `TypeError` between tz-aware and naive timestamps
- All-day entities (`end_at is None`) are never locked
- If `lock_boundary` is None, nothing is locked
- Admin/superadmin bypass evaluated before lock check in `require_not_locked`
- `site` is forward-referenced (`"Site"`) with `noqa: F821` to avoid circular import between `app.core` and `app.models`
- `site` is duck-typed at runtime; passing an object without `data_locked_before` raises `AttributeError`

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | Reads `site.data_locked_before` | Lock boundary originates from DB |

## Gotchas
- Timezone stripping compares naive local times; if both inputs are tz-aware but in different zones, ordering may be wrong for the same UTC instant
- `action` parameter is interpolated directly into the 403 detail string; do not pass user-controlled values
- Only `SiteRole.admin` qualifies as admin; any other role is treated as non-admin if `is_superadmin` is False
- Entities without `end_at` are completely exempt from locking
