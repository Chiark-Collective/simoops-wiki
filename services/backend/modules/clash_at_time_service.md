---
service: backend
summary: "Recompute clashes at historical wall-clock instant T"
paths: [backend/app/services/clash/clash_at_time_service.py]
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose

Reconstructs entities and rules as they existed at a specific wall-clock time,
then runs the pure clash engine against the reconstructed set.
Powers the rewind-to-revision feature.

## Interface

- `clash_at_time_service.py::ClashAtTimeService.evaluate(site_id, at_time)` → list[dict]
- `clash_at_time_service.py::ClashAtTimeService._reconstruct_rules_at_time(site_id, at_time, profile_id)` → list[ClashRule]
- `clash_at_time_service.py::ClashAtTimeService._reconstruct_tokens_at_time(site_id, at_time)` → list
- `clash_at_time_service.py::ClashAtTimeService._reconstruct_plants_at_time(site_id, at_time)` → list
- `clash_at_time_service.py::ClashAtTimeService._reconstruct_features_at_time(site_id, at_time)` → tuple
- `clash_at_time_service.py::ClashAtTimeService._split_active_and_inactive_cranes(plants, at_time, site_id)` → tuple
- `clash_at_time_service.py::ClashAtTimeService._feature_from_version(v)` → GeometadataFeature
- `clash_at_time_service.py::ClashAtTimeService._rule_from_snapshot(rule_id, snap)` → ClashRule | None
- `clash_at_time_service.py::_uuid_or_none(value)` → UUID | None
- `clash_at_time_service.py::_aware(dt)` → datetime
- `clash_at_time_service.py::_group_has_active_member(plants, window_start, window_end)` → bool

## Internals

- Rule reconstruction combines versioned rules (`clash_rule_versions` latest ≤ T) with legacy live rules that have no version trail
- Versioned rules dropped if operation is `delete` or snapshot has `enabled=false`
- Rules filtered to active profile via snapshot `profile_id`
- Tokens and plants reconstructed from `audit_log` snapshots via `AuditSnapshotReconstructor`
- Features reconstructed from `feature_versions` table directly, bypassing auth checks
- V3.2 inactive cranes: cranes not scheduled within ±30 min of T contribute parked footprint
- Inactive cranes skipped if placed after T or last shift ended >24h before T
- Crane grouping by `schedule_group_id` or `plant.id`

## Touches

| resource | how | why |
|---|---|---|
| postgis | SELECT on `audit_log`, `feature_versions`, `clash_rule_versions`, `sites`, `rule_profiles` | Historical reconstruction |

## Gotchas

- Active profile is taken from LIVE site config; full reconstruction at T is deferred
- Same-contractor exemptions come from LIVE site config, not historical state
- Naive DB datetimes coerced to UTC via `_aware` before comparison to avoid tz mismatches
- Inactive crane persistence uses 24h slack vs live path which uses `query_start`
