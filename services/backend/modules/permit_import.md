---
service: backend
summary: "XLSX permit parsing with config-driven transforms and auto-contractor creation"
paths:
  - backend/app/services/permit_import/service.py
  - backend/app/services/permit_import/parsers/config_loader.py
  - backend/app/services/permit_import/parsers/config_parser.py
  - backend/app/services/permit_import/parsers/transforms.py
flows: [permit_import_flow]
touches: [postgis]
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Parses permit spreadsheets via declarative YAML configs, resolves contractor and location references, and upserts Permit records keyed by (site_id, permit_number).

## Interface
- `backend/app/services/permit_import/service.py::PermitImportService` — upload, list, delete, reconcile
- `backend/app/services/permit_import/service.py::PermitImportService.upload` — parse → resolve → upsert
- `backend/app/services/permit_import/service.py::PermitImportService.re_resolve_locations` — re-match locations against current site features
- `backend/app/services/permit_import/service.py::PermitImportService.reconcile_counts` — fix drifted workers_created_count
- `backend/app/services/permit_import/service.py::PermitImportService.list_formats` — available parser formats
- `backend/app/services/permit_import/parsers/config_loader.py::load_format_configs` — load YAML format definitions
- `backend/app/services/permit_import/parsers/config_loader.py::PermitFormatConfig` — declarative format schema
- `backend/app/services/permit_import/parsers/config_parser.py::ConfigDrivenParser` — XLSX parser driven by config
- `backend/app/services/permit_import/parsers/transforms.py::TRANSFORM_REGISTRY` — named cell transform functions
- `backend/app/services/permit_import/parsers/transforms.py::parse_datetime` — multi-format datetime parsing
- `backend/app/services/permit_import/parsers/transforms.py::split_values` — delimiter splitting
- `backend/app/services/permit_import/parsers/transforms.py::regex_extract` — regex group extraction

## Internals
- Config-driven parser locates headers by case-insensitive match and applies per-column transforms.
- Contractor resolution auto-creates missing contractors by name.
- Location resolution matches raw location strings against site building/zone names; skip-list filters non-locations ("site wide", "n/a", etc.).
- Upsert keys on `(site_id, permit_number)` — existing permits are fully overwritten.
- `re_resolve_locations` re-runs resolution for all site permits after site geometry changes.
- `reconcile_counts` counts actual entities referencing each permit via `created_from_permit` and fixes drift.

## Touches
| resource | how | why |
|---|---|---|
| postgis | SQLModel insert/select/upsert | permit persistence, contractor lookup |
| websocket | `ws_manager.broadcast_to_room` | notify clients of permit count changes |

## Gotchas
- Multiple parsers matching the same extension raises ValueError.
- Blank key rows (permit_number or contractor_name) are skipped when `skip_blank_key_rows` is true.
- Missing required columns fail fast at parse time.
