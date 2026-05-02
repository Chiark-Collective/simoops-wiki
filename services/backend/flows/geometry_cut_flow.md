---
trigger: { channel: http, ref: "POST /features/{id}/cut" }
services: [backend]
contracts: []
external: []
---

## Trigger
Client sends a geometry cut request specifying cutter and target feature IDs.

## Steps
1. FastAPI route authenticates the user and enforces `Permission.entity_edit`.
2. `require_not_locked` checks that the target feature's site and `end_at` are not under data lock.
3. `GeometryCuttingService.cut_hole` loads the cutter and target `GeometadataFeature` rows.
4. `get_effective_type` resolves feature types; `can_cut` verifies an exclusive `LayerTypeRule` exists for the site.
5. PostGIS `ST_Intersects` confirms the two geometries actually overlap.
6. The original target geometry is saved to `GeometryHistory` with operation `cut`.
7. Raw SQL `UPDATE geometadata_features SET geometry = ST_Multi(ST_Difference(...))` executes, bumping `geometry_revision`.
8. `invalidate_and_broadcast` emits an `entity_updated` WebSocket event and schedules clash cache recomputation.

## Side effects
- PostGIS `geometadata_features` row updated for the target.
- `GeometryHistory` row inserted with `geometry_before` and `geometry_after`.
- WebSocket broadcast to site subscribers.
- Clash cache invalidation triggered.

## Failure modes
- No exclusive rule allows the cut → `CutResult(success=False)` returned without DB mutation.
- Geometries do not intersect → `CutResult(success=False)`.
- Concurrent geometry edit → `geometry_revision` mismatch causes in-flight WebSocket vertex ops to be rejected by clients.
- Database integrity error on version table (rare race) → caller should retry or surface 409.
