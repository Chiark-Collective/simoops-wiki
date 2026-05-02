---
trigger: { channel: http, ref: "POST /buildings/{feature_id}/floor-plans/upload" }
services: [backend]
contracts: []
external: []
---

## Trigger
Client uploads a GeoTIFF or image file for a building floor plan level.

## Steps
1. FastAPI route authenticates the user and enforces `Permission.building_edit`.
2. `FloorPlanService.upload_floor_plan` (or `upload_floor_plan_image`) validates that the level exists and is not already occupied.
3. File is staged to S3 via `_stage_upload_to_s3`; oversize files rejected with HTTP 413.
4. A `BuildingFloorPlan` record is created with `status=processing`, persisted, and audited.
5. WebSocket `entity_created` broadcast sent to site subscribers.
6. Background task `process_floor_plan_upload` is enqueued with the floor plan ID and local temp path.
7. Processor resolves the local file (downloading from S3 if necessary).
8. For non-georeferenced images, `cog_builder.georeference_image` computes GCPs from placement params.
9. `cog_builder.create_cog_from_upload` runs `gdalwarp` to EPSG:3857 COG, optionally clipped to the building polygon cutline.
10. COG is uploaded to S3; `tilejson_url` is built via Titiler.
11. `BuildingFloorPlan` is updated with `status=ready`, dimensions, bounds, and URLs.
12. Best-effort audit row captured so revision-mode queries see the post-processing state.

## Side effects
- S3 objects created (original image and COG).
- PostGIS `BuildingFloorPlan` row inserted and updated.
- WebSocket broadcast on initial creation.
- Audit log entries for upload and processing completion.

## Failure modes
- File larger than 500MB → HTTP 413 before staging.
- Level already has a floor plan → HTTP 409.
- GDAL failure or corrupt image → processor catches exception, sets `status=failed`, audits, and logs.
- Missing building geometry → processor skips cutline clipping but continues COG generation.
- S3 deletion failure during cleanup → logged but not raised.
