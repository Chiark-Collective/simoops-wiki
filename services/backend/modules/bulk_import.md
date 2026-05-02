---
service: backend
summary: "CSV/GeoJSON bulk ingest pipeline for workers, plant, areas, and references"
paths:
  - backend/app/services/bulk_import/service.py
  - backend/app/services/bulk_import/parser.py
  - backend/app/services/bulk_import/validator.py
  - backend/app/services/bulk_import/resolver.py
  - backend/app/services/bulk_import/builder.py
  - backend/app/services/bulk_import/detector.py
  - backend/app/services/bulk_import/building_resolver.py
  - backend/app/services/bulk_import/cad_polygonize.py
flows: [bulk_import_flow]
touches: [postgis]
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Orchestrates two-phase bulk import: validate parses and caches resolved rows; execute builds domain models and persists them. Supports CSV, GeoJSON, and CAD-exported GeoJSON.

## Interface
- `backend/app/services/bulk_import/service.py::BulkImportService` — validate-then-execute orchestrator
- `backend/app/services/bulk_import/service.py::BulkImportService.validate` — run full validation pipeline
- `backend/app/services/bulk_import/service.py::BulkImportService.execute` — persist cached import
- `backend/app/services/bulk_import/service.py::BulkImportService.compute_schema_warnings` — schema drift detection
- `backend/app/services/bulk_import/parser.py::parse_csv` — CSV → list[ImportRow]
- `backend/app/services/bulk_import/parser.py::parse_geojson` — GeoJSON → list[ImportRow]
- `backend/app/services/bulk_import/parser.py::parse_geojson_with_metadata` — GeoJSON + simoops_metadata
- `backend/app/services/bulk_import/resolver.py::NameResolver` — batch name-to-UUID resolution
- `backend/app/services/bulk_import/resolver.py::NameResolver.load_lookups` — load site contractors, shifts, buildings, zones
- `backend/app/services/bulk_import/resolver.py::NameResolver.resolve_rows` — resolve ImportRow batch
- `backend/app/services/bulk_import/validator.py::validate_rows` — per-row validation
- `backend/app/services/bulk_import/builder.py::build_entities` — ResolvedRow → domain models
- `backend/app/services/bulk_import/builder.py::build_reference_feature` — reference feature builder
- `backend/app/services/bulk_import/detector.py::detect_intra_file_duplicates` — same-file duplicate warnings
- `backend/app/services/bulk_import/detector.py::detect_db_duplicates` — existing DB duplicate warnings
- `backend/app/services/bulk_import/building_resolver.py::resolve_building_for_entities` — spatial building_feature_id assignment
- `backend/app/services/bulk_import/cad_polygonize.py::polygonize_cad_geojson` — CAD LineString → Polygon conversion

## State
In-memory validated-import cache `_import_cache` maps import_id → `_CachedImport`.
- Entries expire after 30 minutes (`_CACHE_TTL_SECONDS`).
- `_CachedImport` holds `resolved_rows`, `row_results`, `layers_metadata`.
- Cleanup is lazy on validate/execute entry.
- Invariant: cache expiry → execute raises ValueError; client must re-validate.

## Internals
- Parser drops `building_feature_id` from GeoJSON source — foreign UUIDs are not portable across sites.
- `building_resolver.py` restores `building_feature_id` by point-in-polygon test against site buildings; smallest containing polygon wins.
- `NameResolver` position priority: explicit lon/lat > building centroid > zone centroid.
- Temporal resolution priority: explicit ISO start_at/end_at > shift+date > all-day.
- `detect_db_duplicates` uses two-tier detection: Tier 1 source_id (UUID) for GeoJSON round-trips; Tier 2 composite key for CSV/manual imports.
- CAD preprocessor detects LineString + text Point features without entity_type; stitches outlines via `shapely.ops.polygonize` and labels polygons by point-in-polygon text placement.
- FeatureVersion snapshots are created for every imported `GeometadataFeature`.
- Audit entries are written per persisted entity with `snapshot_entity_for_storage`.

## Touches
| resource | how | why |
|---|---|---|
| postgis | SQLModel insert/select | persist entities, resolve lookups, duplicate detection |

## Gotchas
- Schema version mismatch triggers a warning but does not block import.
- Data lock boundary rejects rows whose `end_at` falls in the locked period unless user is admin/superadmin.
- `skip_errors=false` with any error row causes execute to raise ValueError.
- Reference features require `layers_metadata` from GeoJSON `simoops_metadata` block.
