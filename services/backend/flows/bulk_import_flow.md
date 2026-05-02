---
trigger: { channel: http, ref: "POST /api/sites/{site_id}/imports/bulk" }
services: [backend]
contracts: []
external: []
---

## Trigger
User uploads a CSV or GeoJSON file via HTTP.

## Steps
1. `bulk_import/parser.py::parse_csv` or `bulk_import/parser.py::parse_geojson_with_metadata` extracts `list[ImportRow]` + optional metadata.
2. `bulk_import/cad_polygonize.py::polygonize_cad_geojson` pre-processes CAD exports (LineString → Polygon).
3. `bulk_import/resolver.py::NameResolver.load_lookups` fetches site contractors, shifts, buildings, zones.
4. `bulk_import/resolver.py::NameResolver.resolve_rows` converts names to UUIDs and computes positions/temporal fields.
5. `bulk_import/detector.py::detect_intra_file_duplicates` flags same-file duplicates.
6. `bulk_import/detector.py::detect_db_duplicates` flags existing DB duplicates by source_id or composite key.
7. `bulk_import/validator.py::validate_rows` checks required fields, enums, geometry, and layer refs.
8. `bulk_import/service.py::BulkImportService.validate` caches resolved rows in `_import_cache` and returns `ValidateResponse`.
9. Client reviews preview and calls execute with `import_id`.
10. `bulk_import/service.py::BulkImportService.execute` retrieves cache, filters excluded/error rows, applies data-lock check.
11. `bulk_import/builder.py::build_entities` converts valid rows to domain models.
12. `bulk_import/building_resolver.py::resolve_building_for_entities` assigns `building_feature_id` by point-in-polygon.
13. `bulk_import/service.py::_resolve_layers` matches/creates `GeometadataLayer` records for reference features.
14. `bulk_import/builder.py::build_reference_feature` creates reference features with resolved layer_id.
15. `bulk_import/service.py` flushes and commits all entities, creates `FeatureVersion` for areas, writes audit entries.
16. Cache entry is removed.

## Side effects
- Inserts into `Worker`, `Plant`, `GeometadataFeature`, `Delivery`, `PointOfInterest`, `TextLabel`.
- Creates `FeatureVersion` rows for imported areas.
- Writes `AuditAction.created` entries per entity.
- Removes `_import_cache` entry on success or expiry.

## Failure modes
- Parse error → empty or malformed file returns error before caching.
- Resolver error → row gets `RowStatus.error` (e.g., contractor not found).
- Validation error → same; execute rejects unless `skip_errors=true`.
- Cache expiry → execute raises ValueError; user must re-validate.
- Data lock → rows with `end_at` inside locked period are silently skipped (counted in `skipped_count`).
- DB duplicate warning → row gets `RowStatus.warning` but is still importable.
