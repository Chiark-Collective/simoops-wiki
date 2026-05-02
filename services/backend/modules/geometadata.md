---
service: backend
summary: GeoJSON/SHP feature management with RBAC, versioning, and broadcasting.
paths:
  - backend/app/services/geometadata/geometadata_feature_service.py
  - backend/app/services/geometadata/geometadata_layer_service.py
  - backend/app/services/geometadata/geometadata_parser.py
  - backend/app/services/geometadata/feature_query_service.py
  - backend/app/services/geometadata/feature_versioning_service.py
  - backend/app/services/geometadata/feature_level_service.py
  - backend/app/services/geometadata/feature_serializer.py
  - backend/app/services/geometadata/feature_broadcast.py
flows:
  - services/backend/flows/geometry_cut_flow.md
touches:
  - PostGIS
  - WebSocket
  - Clash cache
external: []
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Manages geometadata features and layers: CRUD, bulk GeoJSON/Shapefile import, optimistic concurrency, building levels, temporal versioning, and real-time broadcasting.

## Interface
- `geometadata_feature_service.py::FeatureCrudService`
  - `create_zone_feature`
  - `update_feature`
  - `delete_feature`
  - `restore_feature`
- `geometadata_feature_service.py::ensure_building_has_levels`
- `geometadata_layer_service.py::LayerService`
  - `upload_layer`
  - `list_layers`
  - `create_layer`
  - `get_layer`
  - `update_layer`
  - `delete_layer`
- `geometadata_parser.py::process_geojson`
- `geometadata_parser.py::process_shapefile_zip`
- `geometadata_parser.py::ProcessedFeature`
- `geometadata_parser.py::ProcessingResult`
- `feature_query_service.py::FeatureQueryService`
  - `find_building_at_point`
  - `get_distinct_levels`
  - `get_feature_count`
  - `list_layer_features`
  - `list_features_by_type`
  - `get_feature`
  - `list_areas`
  - `get_building_at_point`
  - `list_features_at_time`
  - `get_feature_history`
  - `get_feature_at_time`
  - `cleanup_old_versions`
- `feature_query_service.py::layer_to_read`
- `feature_query_service.py::layers_to_read_batch`
- `feature_versioning_service.py::create_feature_version`
- `feature_versioning_service.py::cleanup_old_versions`
- `feature_level_service.py::apply_level_update`
- `feature_serializer.py::feature_to_read`
- `feature_serializer.py::feature_to_summary`
- `feature_serializer.py::version_to_read`
- `feature_broadcast.py::broadcast_feature_event`
- `feature_broadcast.py::invalidate_and_broadcast`
- `feature_broadcast.py::invalidate_clash_cache`

## Internals
- `FeatureCrudService.create_zone_feature` validates polygon/line geometry via `geometry.py` helpers and auto-sets `clashable` from feature type.
- `update_feature` implements optimistic concurrency with `expected_updated_at`; overlapping semantic field groups raise 409, non-overlapping changes auto-merge.
- `delete_feature` tombstones planned features (`plan_state='planned'`) via `tombstoned_at`; baseline/actual features are hard-deleted.
- Layer upload accepts `.geojson`, `.json`, or `.zip` (shapefile), auto-detects CRS, and caps at 10 000 features.
- Parser promotes closed LineStrings to Polygons and assembles open LineStrings via `shapely.ops.polygonize`; labels matched to polygons for naming.
- `create_feature_version` closes the current version (`valid_to = now`) and inserts a new snapshot; `create` operations use epoch `valid_from` so features appear at all historical scrubber positions.
- A partial unique index on `(feature_id) WHERE valid_to IS NULL` guarantees at most one current version per feature.
- `apply_level_update` remaps `Worker`, `Plant`, and child `GeometadataFeature` building levels; removal blocked if entities occupy the level.
- `feature_to_read` converts WKB geometry to WGS84 coordinate arrays; `version_to_read` synthesises `revision_hash` from the version UUID.

## Touches
| resource | how | why |
| PostGIS | `ST_Contains`, `ST_Intersects`, geometry columns | spatial storage and queries |
| WebSocket | `ws_manager.broadcast_entity_event` | real-time feature updates to clients |
| Clash cache | `clash_cache.schedule_recomputation` | invalidate on any mutation |

## Gotchas
- `process_geojson` silently drops unsupported geometry types.
- Shapefile processing requires Fiona; missing dependency raises `ImportError`.
- `expected_updated_at` auto-merge only works when client and server field groups do not overlap.
- Tombstoned features must be restored via `restore_feature`, not recreated.
