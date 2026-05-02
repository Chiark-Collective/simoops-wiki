---
trigger: { channel: websocket, ref: "action: vertex_op" }
services: [backend]
contracts: []
external: []
---

## Trigger
WebSocket message with `action: "vertex_op"` carrying a vertex operation (move,
insert, or delete) for a polygon feature.

## Steps
1. `websocket.py::_handle_vertex_op` requires an active room subscription
2. Parses `feature_id`, `op_type`, `base_rev`, and `expected_geom_rev`
3. Loads the feature from PostGIS to verify RBAC (`Permission.entity_edit`) and geometry revision gate
4. Calls `vertex_op_service.py::VertexOpService.handle_vertex_op`
5. `vertex_op_store.py::transform_and_record` transforms the incoming op against missed concurrent ops via OT
6. Transformed op applied to the feature's exterior ring; validated via `polygon_from_lonlat`
7. Geometry persisted to PostGIS; `geometry_revision` incremented implicitly
8. `audit_service.py::AuditService.record` writes an audit entry for the geometry edit
9. `websocket_runtime::ws_manager.broadcast_ephemeral` emits `vertex_op_applied` to all subscribers except sender
10. Sender receives `vertex_op_ack` with new `rev` and updated `polygon_wgs84`

## Side effects
- PostGIS UPDATE of `GeometadataFeature.geometry`
- Audit log INSERT with geometry change summary
- Redis ephemeral broadcast of `vertex_op_applied`
- OT state mutation in `vertex_op_buffer` (in-memory or Redis)

## Failure modes
| Failure | Detection | Handling |
|---|---|---|
| Stale revision | `base_rev` too old (gap > max_ops) | `vertex_op_ack` with `stale: true`, client reloads |
| Geometry revision mismatch | `expected_geom_rev != current_geom_rev` | `vertex_op_ack` with `stale: true` |
| OT CAS contention | Redis Lua CAS returns -1 after 5 retries | `RuntimeError` logged; client receives generic error |
| Invalid polygon after op | `< 3 vertices` or self-intersection | `vertex_op_ack` with error message |
| Forbidden | `entity_edit` missing or global feature | `vertex_op_ack` with `reason: forbidden` |
| Feature not found | Missing `GeometadataFeature` row | `vertex_op_ack` with `reason: feature_not_found` |
