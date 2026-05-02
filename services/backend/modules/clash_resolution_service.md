---
service: backend
summary: "Clash resolution persistence and annotation"
paths: [backend/app/services/clash/clash_resolution_service.py]
flows: [clash_detect_and_resolve]
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose

Persists user resolutions of clashes and annotates computed clash dicts with
resolved state. Provides stable canonical keys for clash identity.

## Interface

- `clash_resolution_service.py::resolve_clash(session, site_id, entity_id_a, entity_id_b, rule_name, resolved_by, note)` → `ClashResolution`
- `clash_resolution_service.py::unresolve_clash(session, site_id, entity_id_a, entity_id_b, rule_name)` → `UnresolveResult`
- `clash_resolution_service.py::get_resolutions_for_site(session, site_id)` → dict
- `clash_resolution_service.py::filter_resolved_clashes(clashes, resolutions)` → list[dict]
- `clash_resolution_service.py::annotate_clashes_with_resolutions(clashes, resolutions)` → None (mutates in place)
- `clash_resolution_service.py::canonical_clash_key(id_a, id_b)` → tuple[str, str]
- `clash_resolution_service.py::UnresolveResult` — dataclass with `deleted` and `resolution_id`

## Internals

- Upsert semantics: re-resolving updates `note` and `resolved_by` on existing row
- Canonical key sorts entity IDs as `(lo, hi)` so (A,B) and (B,A) match stably
- `clash_resolutions` identity: `(site_id, entity_lo, entity_hi, rule_name)`
- Entity IDs stored as strings because they span tokens, plants, zones, and synthetic inactive cranes
- `annotate_clashes_with_resolutions` mutates clash dicts in place adding `resolved`, `resolved_at`, `resolved_by`

## Touches

| resource | how | why |
|---|---|---|
| postgis | INSERT/UPDATE/DELETE on `clash_resolutions` | Persist resolution state |

## Gotchas

- Entity IDs are strings, not UUID FKs
- Resolution is site-wide; all users see the same resolved state
- `unresolve_clash` returns `UnresolveResult(deleted=False)` when no resolution exists
