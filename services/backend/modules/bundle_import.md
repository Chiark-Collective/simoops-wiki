---
service: backend
summary: ".sob bundle ingest: buildings, reference layers, and floor plans"
paths:
  - backend/app/services/bundle_import/service.py
  - backend/app/services/bundle_import/parser.py
  - backend/app/services/bundle_import/validator.py
  - backend/app/services/bundle_import/idempotency.py
  - backend/app/services/bundle_import/floor_plan_writer.py
flows: [bundle_import_flow]
touches: [postgis, minio]
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Imports SimOops building bundles (.sob zip) containing manifest, vector GeoJSON, and raster floor plans. Validates zip safety, decides create/update/no_op per building and layer, then persists with deferred COG processing.

## Interface
- `backend/app/services/bundle_import/service.py::BundleImportService` — validate-then-execute orchestrator
- `backend/app/services/bundle_import/service.py::BundleImportService.validate_from_path` — parse + validate + cache
- `backend/app/services/bundle_import/service.py::BundleImportService.execute` — persist buildings, layers, floor plans
- `backend/app/services/bundle_import/service.py::BundleImportService.cancel` — drop cached import without executing
- `backend/app/services/bundle_import/parser.py::parse_bundle` — zip → ParsedBundle
- `backend/app/services/bundle_import/parser.py::ParsedBundle` — manifest + extracted members + scratch dir
- `backend/app/services/bundle_import/validator.py::validate_bundle` — cross-reference manifest against DB state
- `backend/app/services/bundle_import/idempotency.py::decide_building_action` — create/update/no_op for buildings
- `backend/app/services/bundle_import/idempotency.py::decide_layer_action` — create/update for layers
- `backend/app/services/bundle_import/idempotency.py::compute_geometry_diff_m2` — symmetric-difference area
- `backend/app/services/bundle_import/floor_plan_writer.py::path_to_upload_file` — path → UploadFile adapter

## State
In-memory cache `_import_cache` maps import_id → `_CachedImport`.
- 30-minute TTL; cleanup removes scratch directories on expiry.
- `_CachedImport` holds `ParsedBundle` (owns temp dir), `BundleValidationResult`.
- Invariant: cache miss or site mismatch → execute raises KeyError/PermissionError.

## Internals
- Zip safety enforces compressed ≤250 MB, single member ≤600 MB, total ≤5 GB; rejects zip-slip paths.
- Manifest drives building and layer definitions; vector files are parsed via `process_geojson`.
- Building idempotency uses `properties.bundle_id` match; geometry changes below 1 m² threshold → no_op.
- Layer idempotency uses `extra.bundle_id`; re-import always replaces features (no no_op).
- Floor plans commit after buildings so feature_ids exist; COG processing is deferred via `background_tasks`.
- PNG/JPEG floor plans require placement parameters; GeoTIFF flows through georeferenced upload.

## Touches
| resource | how | why |
|---|---|---|
| postgis | SQLModel insert/update/delete | buildings, layers, features, floor plans |
| minio | S3 upload via FloorPlanService | raster storage |

## Gotchas
- Scratch directories are leaked if the process crashes before cleanup.
- Raster files not referenced by any level are flagged as orphans.
- Multiple convention-named rasters for the same level raise ValueError.
- Building update bumps `geometry_revision` and writes FeatureVersion + audit.
