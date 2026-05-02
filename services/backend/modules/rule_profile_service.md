---
service: backend
summary: "Rule profile resolution and CRUD orchestration"
paths: [backend/app/services/clash/rule_profile_service.py]
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose

Resolves the active rule profile for a site via fallback chain, and owns
persistence, audit, and broadcast for profile create/update/delete/activate/clone.

## Interface

- `rule_profile_service.py::get_active_profile(session, site_id)` → `RuleProfile | None`
- `rule_profile_service.py::RuleProfileCrudService(session)` — profile CRUD + clone
- `rule_profile_service.py::RuleProfileCrudService.create_profile(user, payload, membership)` → `RuleProfile`
- `rule_profile_service.py::RuleProfileCrudService.update_profile(user, profile, payload, membership)` → `(RuleProfile, int)`
- `rule_profile_service.py::RuleProfileCrudService.delete_profile(user, profile, membership)` → None
- `rule_profile_service.py::RuleProfileCrudService.activate_profile(user, profile, membership)` → `(RuleProfile, int)`
- `rule_profile_service.py::RuleProfileCrudService.clone_profile(user, source, payload, membership)` → `(RuleProfile, int)`
- `rule_profile_service.py::_deactivate_other_profiles(session, site_id, exclude_profile_id)` → None

## State

None. Persistent state in `rule_profiles` table.

## Internals

- Fallback chain: site-specific active → system-wide active → "Standard" system profile
- `_deactivate_other_profiles` flushes before returning to satisfy partial unique index `uq_rule_profile_active_per_site`
- System profiles (`is_system=True`) cannot be edited or deleted
- `update_profile` triggers `clash_cache.schedule_recomputation` when `is_active` changes
- `delete_profile` unassigns rules by setting `profile_id=None` before deleting
- `clone_profile` creates new profile and copies rules, then creates version records via `RuleVersionService`
- Audit records created for site-scoped mutations; broadcast via `broadcast_config_event`

## Touches

| resource | how | why |
|---|---|---|
| postgis | CRUD on `rule_profiles`, `clash_rules` | Profile and rule persistence |
| websocket_runtime | `broadcast_config_event` | Push `rule_profile` domain events |
| clash_cache | `schedule_recomputation` | Activation invalidates detection cache |

## Gotchas

- System profiles locked: `ValueError("system_profile_locked")` on name/description edit
- System profiles undeletable: `ValueError("system_profile_undeletable")`
- Partial unique index requires explicit flush between deactivation and activation
- Clone operation creates version records for each cloned rule
