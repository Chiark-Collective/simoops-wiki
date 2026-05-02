---
trigger: { channel: http, ref: "POST /api/sites/{site_id}/permits/upload" }
services: [backend]
contracts: []
external: []
---

## Trigger
User uploads an XLSX permit file via HTTP.

## Steps
1. `permit_import/service.py::PermitImportService.upload` receives file bytes and optional `format_id`.
2. If `format_id` is provided, look up in `PARSER_REGISTRY`; else auto-detect by extension.
3. `permit_import/parsers/config_parser.py::ConfigDrivenParser.parse` opens workbook, matches headers, applies transforms.
4. `permit_import/parsers/transforms.py` functions coerce datetimes, split lists, strip strings, extract regex groups.
5. `permit_import/service.py` creates a `PermitSet` record.
6. `permit_import/resolver.py::PermitResolver.load_lookups` fetches site contractors and features.
7. `permit_import/resolver.py::PermitResolver.resolve_contractor` matches name or auto-creates contractor.
8. `permit_import/resolver.py::PermitResolver.resolve_location` matches raw string against building/zone names.
9. `permit_import/service.py` upserts each permit by `(site_id, permit_number)` — insert new or update existing.
10. `permit_import/service.py` commits and returns `PermitUploadResponse`.

## Side effects
- Inserts/updates `Permit` rows.
- Inserts `Contractor` rows when auto-created.
- Creates `PermitSet` record tracking upload metadata.
- WebSocket broadcast `permit_count_updated` to site room when counts change.

## Failure modes
- Unknown format_id or ambiguous extension → ValueError before parsing.
- Missing required columns → ValueError from `_build_column_index`.
- Empty file → ValueError if no permit rows found.
- Unresolved location → tracked in `unresolved_locations` but does not block import.
- Re-resolve after site geometry changes may shift matched_feature_id; `re_resolve_locations` updates in bulk.
