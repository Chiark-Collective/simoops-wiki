---
service: backend
summary: "Rule CRUD, versioning, profiles, DSL generation, and utilities"
paths: [
  backend/app/services/clash/clash_rule_service.py,
  backend/app/services/clash/rule_version_service.py,
  backend/app/services/clash/rule_profile_service.py,
  backend/app/services/clash/dsl_generator.py,
  backend/app/services/clash/clash_rule_utils.py,
  backend/app/services/clash/clash_rule_serializer.py,
  backend/app/services/clash/layer_type_merge.py,
]
flows: []
touches: []
external: []
last_verified_commit: TBD
---

# Clash Rules

## Purpose

Manage clash rules, their version history, active profiles, and
human-readable representations. Provide validation, YAML import/export,
and site-specific layer-type merging.

## Interface

- `clash_rule_service.py::ClashRuleService(session)` — CRUD + YAML import + detection
- `clash_rule_service.py::ClashRuleService.query_rules(site_id, include_global, enabled_only)` → list
- `clash_rule_service.py::ClashRuleService.create_rule(payload)` → `ClashRule`
- `clash_rule_service.py::ClashRuleService.apply_updates(rule, payload)` → None
- `clash_rule_service.py::ClashRuleService.import_from_yaml(yaml, site_id, replace_existing)` → `(rules, warnings)`
- `clash_rule_service.py::ClashRuleService.load_and_import_defaults(site_id, replace_existing)` → `(rules, warnings)`
- `rule_version_service.py::RuleVersionService(session)` — audit trail for rule changes
- `rule_version_service.py::RuleVersionService.create_version(rule, operation, user_id, changes_summary)` → `ClashRuleVersion`
- `rule_version_service.py::RuleVersionService.revert_to_version(rule_id, version, user_id)` → `ClashRule`
- `rule_version_service.py::RuleVersionService.compute_diff(rule_id, version_a, version_b)` → dict
- `rule_profile_service.py::get_active_profile(session, site_id)` → `RuleProfile | None`
- `rule_profile_service.py::RuleProfileCrudService(session)` — profile CRUD + clone
- `rule_profile_service.py::RuleProfileCrudService.create_profile(user, payload, membership)` → `RuleProfile`
- `rule_profile_service.py::RuleProfileCrudService.update_profile(user, profile, payload, membership)` → `(profile, rule_count)`
- `rule_profile_service.py::RuleProfileCrudService.activate_profile(user, profile, membership)` → `(profile, rule_count)`
- `rule_profile_service.py::RuleProfileCrudService.clone_profile(user, source, payload, membership)` → `(profile, count)`
- `dsl_generator.py::DslGenerator.generate(rule)` → human-readable DSL text
- `dsl_generator.py::DslGenerator.generate_yaml(rule)` → YAML representation
- `clash_rule_utils.py::validate_predicates(predicates)` → bool
- `clash_rule_utils.py::parse_yaml_rule(data, site_id)` → `ClashRule`
- `clash_rule_serializer.py::rule_to_read(rule)` → `ClashRuleRead`
- `clash_rule_serializer.py::profile_to_read(profile, rule_count)` → `RuleProfileRead`
- `layer_type_merge.py::merge_global_and_site_rows(session, model_class, site_id, key_fn)` → list

## State

None at module level. Version history and profiles are persistent DB state.

## Internals

- `ClashRuleService.create_rule` validates predicates via `validate_predicates`
- `ClashRuleService.import_from_yaml` supports `replace_existing` to delete prior rules
- Default rules loaded from `backend/app/engine/default_rules.yaml`
- `RuleVersionService.create_version` serializes rule to JSON snapshot
- `_get_next_version` uses PostgreSQL advisory lock (`pg_advisory_xact_lock`) to prevent duplicate version numbers
- `_rule_to_snapshot` coerces enums to strings for uniform serialization
- `revert_to_version` is non-destructive: creates a new version with restored state
- `get_active_profile` fallback chain: site-specific active → system-wide active → "Standard" system profile
- `_deactivate_other_profiles` flushes before returning to satisfy partial unique index `uq_rule_profile_active_per_site`
- `RuleProfileCrudService.update_profile` triggers `clash_cache.schedule_recomputation` when `is_active` changes
- `RuleProfileCrudService.clone_profile` copies all rules and creates version records for each
- `DslGenerator` maps entity kind+types to readable labels and predicates to verbs
- `merge_global_and_site_rows` dedupes by `key_fn` so site rows shadow globals

## Touches

| resource | how | why |
|---|---|---|
| [websocket_runtime](websocket_runtime.md) | `broadcast_config_event` | Push `rule_profile` create/update/delete/activate events |
| [core_rbac](core_rbac.md) | Route-level permission checks | HTTP routes verify `clash_rule.*` permissions |
| [clash_detection](clash_detection.md) | `clash_cache.schedule_recomputation` | Profile activation invalidates detection cache |

## Gotchas

- System profiles cannot be edited (`system_profile_locked`) or deleted (`system_profile_undeletable`)
- Advisory lock is transaction-scoped; version allocation is atomic per rule but not across rules
- YAML import does not validate predicate semantics beyond structure; invalid rules fail at compile time
- `merge_global_and_site_rows` assumes `.site_id` column exists on `model_class`
