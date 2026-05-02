---
trigger: { channel: websocket, ref: "entity_created or entity_updated event" }
services: [backend]
contracts: []
external: []
---

# Clash Detect and Resolve

## Trigger

WebSocket `entity_created` or `entity_updated` event, or HTTP POST to `/api/clash-rules/{id}/evaluate`.

## Steps

1. `ClashDetectionService` receives trigger (async task or sync call)
2. Loads active rules for site from `ClashRuleService`
3. `RuleCompiler(site)` compiles DB rules into `CompiledRule` runtime objects
4. Loads relevant entities for current shift + time slice
5. `DeclarativeClashEngine(compiled_rules)` evaluates entity set
6. R-tree broad-phase filters to overlapping AABB pairs
7. Narrow-phase predicates evaluated per pair
8. `ClashCache` stores results keyed by `(site_id, shift_id, timestamp)`
9. `ClashResolutionService` compares new results against cached prior state
10. Deltas (new / resolved / updated) emitted via WebSocket `clash_updated`

## Side effects

- PostGIS INSERT/UPDATE into `clashes` table
- Redis cache write (`ClashCache`)
- WebSocket broadcast to `site:{site_id}` room
- Audit log entry for manual rule evaluations

## Failure modes

| Failure | Detection | Handling |
|---|---|---|
| Rule compilation error | Exception in `RuleCompiler` | Logged; rule skipped; evaluation continues |
| Empty entity set | No entities in shift | Returns `[]`; no broadcast |
| Cache stale | Timestamp mismatch | Recompute from scratch |
| Engine timeout | CPU-bound on large site | Task cancelled; clashes remain stale |
