---
service: backend
summary: Polygon cutting, floor plan processing, and geometry operations.
paths:
  - backend/app/services/geometadata/geometry_cutting.py
  - backend/app/services/geometadata/geometry.py
  - backend/app/services/geometadata/floor_plan_service.py
  - backend/app/services/geometadata/floor_plan_processor.py
  - backend/app/services/geometadata/floor_plan_at_time_resolver.py
flows:
  - services/backend/flows/geometry_cut_flow.md
  - services/backend/flows/floor_plan_upload_flow.md
touches:
  - PostGIS
  - S3
  - WebSocket
  - Audit log
external: []
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Provides geometry exclusivity cutting, coordinate transformation, and floor plan raster upload/COG pipeline.

## Interface
- `geometry_cutting.py::GeometryCuttingService`
  - `get_effective_type`
  - `get_rule`
  - `can_cut`
  - `get_pending_cuts`
  - `cut_hole`
  - `undo_cut`
  - `get_feature_history`
  - `check_overlaps`
- `geometry_cutting.py::CutResult`
- `geometry_cutting.py::PendingCut`
- `geometry_cutting.py::OverlapInfo`
- `geometry.py::to_wgs84_transformer`
- `geometry.py::to_3857_transformer`
- `geometry.py::reproject_geometry`
- `geometry.py::ensure_multipolygon`
- `geometry.py::geometry_to_wgs84_coords`
- `geometry.py::line_geometry_to_wgs84_coords`
- `geometry.py::polygon_from_lonlat`
- `geometry.py::line_from_lonlat`
- `geometry.py::point_to_wkb`
- `geometry.py::wkb_to_point`
- `geometry.py::lonlat_to_wkb`
- `geometry.py::wkb_to_lonlat`
- `floor_plan_service.py::FloorPlanService`
  - `list_floor_plans`
  - `get_floor_plan`
  - `upload_floor_plan`
  - `upload_floor_plan_image`
  - `update_placement`
  - `delete_floor_plan`
  - `get_image_url`
- `floor_plan_processor.py::process_floor_plan_upload`
- `floor_plan_processor.py::_process_floor_plan_logic`
- `floor_plan_at_time_resolver.py::resolve_floor_plan_cog_at_time`

## State
- `floor_plan_at_time_resolver.py` maintains an in-process TTL cache `_CACHE` keyed by `(floor_plan_id, at_time_minute_iso)` with 120-second expiry.
  - Invariant: bucket rounds to the minute to match frontend scrubber granularity.

## Internals
- `cut_hole` stores the original geometry in `GeometryHistory`, then executes `ST_Difference` via raw SQL and bumps `geometry_revision`.
- `undo_cut` restores geometry from `GeometryHistory.geometry_before` and bumps `geometry_revision`.
- `check_overlaps` queries site-specific and global `LayerTypeRule` records to determine exclusivity behavior.
- `geometry.py` caches `pyproj.Transformer` instances at module level to avoid per-call construction cost.
- `FloorPlanService` stages uploads to S3 via tempfiles; supports pre-georeferenced GeoTIFF and non-georeferenced images with placement parameters.
- `floor_plan_processor` georeferences plain images via GCPs (`cog_builder.georeference_image`), then builds a COG clipped to the building polygon cutline.
- `resolve_floor_plan_cog_at_time` walks `audit_log` to find the latest pre-T snapshot; returns `None` for deletions or processing windows.

## Touches
| resource | how | why |
| PostGIS | `ST_Difference`, `ST_Intersects`, geometry columns | cutting and overlap checks |
| S3 | `storage.upload_file`, `storage.delete_file` | raster and COG storage |
| WebSocket | `ws_manager.broadcast_entity_event` | floor plan CRUD events |
| Audit log | `AuditService.record`, direct `AuditLog` writes | state history for revision mode |

## Gotchas
- `cut_hole` requires an exclusive `LayerTypeRule`; otherwise returns `CutResult(success=False)`.
- `geometry_revision` increments on every geometry mutation to invalidate stale WebSocket vertex operations.
- Floor plan processor audit writes are best-effort; failures are logged but do not stop COG generation.
- `resolve_floor_plan_cog_at_time` returns `None` if the latest audit row at `T` is a deletion or lacks a `cog_url`.
