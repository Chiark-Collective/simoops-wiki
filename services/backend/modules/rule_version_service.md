---
service: backend
summary: "Clash rule version history and revert"
paths: [backend/app/services/clash/rule_version_service.py]
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose

Creates version snapshots when rules change, supports history viewing,
diffing, and non-destructive revert to previous versions.

## Interface

- `rule_version_service.py::RuleVersionService(session)` — version management
- `rule_version_service.py::RuleVersionService.create_version(rule, operation, user_id, changes_summary)` → `ClashRuleVersion`
- `rule_version_service.py::RuleVersionService.get_history(rule_id, limit)` → list[ClashRuleVersion]
- `rule_version_service.py::RuleVersionService.get_version(rule_id, version)` → `ClashRuleVersion | None`
- `rule_version_service.py::RuleVersionService.get_latest_version(rule_id)` → `ClashRuleVersion | None`
- `rule_version_service.py::RuleVersionService.revert_to_version(rule_id, version, user_id)` → `ClashRule`
- `rule_version_service.py::RuleVersionService.compute_diff(rule_id, version_a, version_b)` → dict
- `rule_version_service.py::RuleVersionService.auto_summarize_changes(old_snapshot, new_snapshot)` → str
- `rule_version_service.py::RuleVersionService._get_next_version(rule_id)` → int
- `rule_version_service.py::RuleVersionService._rule_to_snapshot(rule)` → dict

## State

None. Persistent state in `clash_rule_versions` table.

## Internals

- `_get_next_version` uses PostgreSQL advisory lock (`pg_advisory_xact_lock`) per rule to prevent duplicate version numbers
- `_rule_to_snapshot` coerces enums to strings for uniform serialization
- `revert_to_version` is non-destructive: creates a new version with restored state
- `auto_summarize_changes` detects name, severity, enabled, priority, predicate, entity type, and message template changes
- `compute_diff` compares snapshot JSON directly; returns changed fields with old/new values
- No FK constraint on `rule_id` in `clash_rule_versions` to allow history for deleted rules

## Touches

| resource | how | why |
|---|---|---|
| postgis | INSERT/SELECT on `clash_rule_versions` | Version persistence and retrieval |

## Gotchas

- Advisory lock is transaction-scoped; version allocation is atomic per rule but not across rules
- `clash_rule_versions` has no unique constraint on `(rule_id, version)`; lock is the only guard
- Revert restores snapshot fields individually; new fields added after the snapshot are not cleared
- `auto_summarize_changes` limits summary to first 3 changes
