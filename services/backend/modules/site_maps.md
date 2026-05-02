---
service: backend
summary: COG tiles, map layers, site map processing, label styles, and elevation parsing.
paths:
  - backend/app/services/geometadata/site_map_processor.py
  - backend/app/services/geometadata/cog_builder.py
  - backend/app/services/geometadata/cog.py
  - backend/app/services/geometadata/label_style_service.py
  - backend/app/services/geometadata/site_map_serializer.py
  - backend/app/services/geometadata/elevation_parser.py
  - backend/app/api/routes/site_maps.py
flows:
  - services/backend/flows/floor_plan_upload_flow.md
touches:
  - PostGIS
  - S3
  - GDAL
external:
  - Titiler
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Converts uploaded site map rasters into Cloud-Optimized GeoTIFFs, serves tile metadata, manages per-site label styles, and extracts elevation data from level labels.

## Interface
- `site_map_processor.py::process_site_map_upload`
- `site_map_processor.py::_process_logic`
- `cog_builder.py::create_cog_from_upload`
- `cog_builder.py::georeference_image`
- `cog_builder.py::compute_gcp_corners`
- `cog_builder.py::CogMetadata`
- `cog_builder.py::CogError`
- `cog_builder.py::cleanup_temp`
- `cog_builder.py::_resolve_local_file`
- `cog_builder.py::_gdal_info`
- `cog_builder.py::_upload_to_minio`
- `cog_builder.py::_build_tilejson_url`
- `cog_builder.py::_write_cutline_geojson`
- `cog.py` (re-export hub) — backward-compatible imports for processors and builders.
- `label_style_service.py::LabelStyleService`
  - `get_styles`
  - `upsert_styles`
- `site_map_serializer.py::site_map_to_read`
- `elevation_parser.py::parse_elevation_from_label`
- `elevation_parser.py::backfill_elevations`

## Internals
- `site_map_processor` runs as a background task: resolves the local file, calls `create_cog_from_upload`, and updates `SiteMap` width, height, bounds, and URLs.
- `create_cog_from_upload` shells out to `gdalwarp` for reprojection to EPSG:3857 and COG creation, then uploads to MinIO and builds a Titiler `tilejson.json` URL.
- `georeference_image` uses `gdal_translate` with GCPs derived from center, rotation, and scale; applies Web Mercator latitude correction via `1/cos(lat)`.
- `label_style_service` fills missing categories with hardcoded defaults (`zone`, `entity`, `text`, `object_number`).
- `site_map_serializer` extracts WGS84 polygon rings from WKB bounds using `geoalchemy2.shape.to_shape`.
- `elevation_parser` regex-extracts signed metre values and slash-separated ranges from level labels during GeoJSON import.

## Touches
| resource | how | why |
| PostGIS | `ST_AsGeoJSON` | bounds serialization |
| S3 / MinIO | `storage.upload_file`, `storage.download_file` | COG and raster storage |
| GDAL | `gdalwarp`, `gdal_translate`, `gdalinfo` | reprojection, COG creation, georeferencing |
| Titiler | `_build_tilejson_url` | tile serving endpoint |

## Gotchas
- `create_cog_from_upload` appends `-dstalpha` when a cutline is used and the source lacks an alpha band.
- `compute_gcp_corners` applies `scale_factor = 1/cos(lat)` to compensate for Web Mercator distortion away from the equator.
- Site map upload route enforces a 2000MB limit; floor plan upload enforces 500MB.
- Elevation parsing is best-effort; labels without metre markers leave `elevation_m` as `None`.
