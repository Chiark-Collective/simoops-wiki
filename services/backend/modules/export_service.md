---
service: backend
summary: "GeoJSON export, PDF table builders, clash formatting, and analytics"
paths:
  - backend/app/services/export/geojson.py
  - backend/app/services/export/table_builders.py
  - backend/app/services/export/formatting.py
  - backend/app/services/export/clash_tables.py
  - backend/app/services/export/clash_dedup.py
  - backend/app/services/export/tile_sidebar.py
  - backend/app/services/export/analytics.py
flows: []
touches: [postgis]
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Converts domain models to GeoJSON FeatureCollections and prepares structured data for PDF report tables, clash summaries, tile sidebars, and analytics charts.

## Interface
- `backend/app/services/export/geojson.py::build_site_geojson` — complete FeatureCollection from site entities
- `backend/app/services/export/geojson.py::token_to_feature` — Worker → GeoJSON Feature
- `backend/app/services/export/geojson.py::plant_to_feature` — Plant → GeoJSON Feature
- `backend/app/services/export/geojson.py::area_to_feature` — GeometadataFeature → GeoJSON Feature
- `backend/app/services/export/geojson.py::reference_feature_to_feature` — reference feature → GeoJSON Feature
- `backend/app/services/export/table_builders.py::build_worker_rows` — workers PDF header/rows
- `backend/app/services/export/table_builders.py::build_crane_rows` — cranes PDF header/rows
- `backend/app/services/export/table_builders.py::build_delivery_rows` — deliveries PDF header/rows
- `backend/app/services/export/table_builders.py::build_area_rows` — areas PDF header/rows
- `backend/app/services/export/table_builders.py::build_clash_section_data` — clash table per type
- `backend/app/services/export/clash_tables.py::build_unified_clash_rows` — single unified clash table
- `backend/app/services/export/clash_dedup.py::deduplicate_clashes` — one row per pair, highest severity
- `backend/app/services/export/clash_dedup.py::filter_new_clashes` — remove pairs present in reference
- `backend/app/services/export/clash_dedup.py::group_collapse_clashes` — pair + occurrence_count
- `backend/app/services/export/tile_sidebar.py::compute_tile_sidebar` — tile-scoped contractors/clashes/deliveries
- `backend/app/services/export/tile_sidebar.py::wgs84_to_tile_pixel` — WGS84 → tile pixel coords
- `backend/app/services/export/analytics.py::build_analytics_data` — aggregated chart data
- `backend/app/services/export/analytics.py::build_summary_table_data` — summary statistics + rule grouping
- `backend/app/services/export/formatting.py::format_entity_time_range` — HH:MM-HH:MM display
- `backend/app/services/export/formatting.py::build_token_lookup` — token ID → display metadata
- `backend/app/services/export/formatting.py::build_plant_lookup` — plant ID → display metadata

## Internals
- GeoJSON output is symmetric with `bulk_import.parser` — same property names and metadata block.
- `build_site_geojson` embeds `simoops_metadata` with schema_version and layers when provided.
- PDF table builders strip empty comment/tags columns when all rows are "-".
- Unified clash table formats all clash types into one table with contractor attribution.
- Clash dedup strategies: `deduplicate` (highest severity), `new_only` (delta vs reference), `group_collapse` (count occurrences).
- Tile sidebar filters clashes to those touching at least one entity in the tile, sorted red-first then by distance.
- Analytics computes entity counts, clashes by type/severity, per-contractor counts, and cross-contractor matrices.

## Touches
| resource | how | why |
|---|---|---|
| postgis | read-only WKB→WGS84 conversion | geometry export |

## Gotchas
- Clash dedup loses lower-severity duplicates; use `group_collapse` to preserve counts.
- Contractor name resolution in analytics depends on presence in the contractor list argument.
- Empty comment/tags columns are stripped from PDF tables, shifting column indices.
