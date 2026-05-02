---
service: backend
summary: "Operational-transform polygon vertex editing over WebSocket"
paths:
  - backend/app/services/entity/vertex_op_service.py
  - backend/app/services/entity/vertex_op_store.py
  - backend/app/services/entity/vertex_op_buffer.py
  - backend/app/services/entity/vertex_ot.py
flows:
  - services/backend/flows/vertex_op_flow.md
touches: []
external: []
last_verified_commit: 9b0d86029a07dc6995ab5dc9f883ef48d6346f9b
---

## Purpose
Enables concurrent polygon vertex editing via operational transform (OT).
Clients send vertex operations (move, insert, delete); the server transforms
stale ops against missed concurrent ops, applies the result, persists to
PostGIS, and broadcasts to other subscribers.

## Interface
- `vertex_ot.py::VertexMove(index, from_pos, to_pos)` → dataclass
- `vertex_ot.py::VertexInsert(after_index, position)` → dataclass
- `vertex_ot.py::VertexDelete(index)` → dataclass
- `vertex_ot.py::apply_op(vertices, op)` → list[list[float]]
- `vertex_ot.py::transform(op_a, op_b)` → tuple[Optional[VertexOp], Optional[VertexOp]]
- `vertex_op_buffer.py::FeatureBuffer.transform_and_record(base_rev, op)` → tuple[Optional[VertexOp], int]
- `vertex_op_buffer.py::VertexOpBuffer.current_rev(feature_id)` → int
- `vertex_op_buffer.py::VertexOpBuffer.transform_and_record(feature_id, base_rev, op)` → tuple[Optional[VertexOp], int]
- `vertex_op_store.py::VertexOpStore` — protocol for async OT stores
- `vertex_op_store.py::InMemoryVertexOpStore` — single-worker fallback
- `vertex_op_store.py::RedisVertexOpStore` — multi-worker atomic store
- `vertex_op_service.py::VertexOpService.handle_vertex_op(user, feature_id, feature_id_str, op, base_rev, connection_id, rooms)` → VertexOpResult
- `vertex_op_service.py::VertexOpResult` — success/error/ack/broadcast_event container

## State
`VertexOpBuffer` maintains per-feature ring buffers of recent ops.

| symbol | type | semantics |
|---|---|---|
| `VertexOpBuffer._features` | `dict[str, FeatureBuffer]` | In-memory op history per feature |
| `FeatureBuffer._buffer` | `deque[BufferedOp]` | Ring buffer (maxlen = `max_ops`) |
| `FeatureBuffer._rev` | `int` | Monotonic revision counter per feature |
| `RedisVertexOpStore` | Redis sorted set + counter | Cross-worker shared state; score = rev |

Invariants:
- `base_rev < current_rev - max_ops` → `ValueError` (client must reload)
- `buffered_op.rev` strictly increasing within a `FeatureBuffer`
- Redis CAS retry limit = 5; beyond that → `RuntimeError` (pathological contention)

## Internals
- `transform` follows server-priority convention: `op_a` applied first, `op_b` adjusted
- Move×Move tie-break: lower `to_pos` (lexicographic) wins; loser becomes no-op
- Insert×Insert tie-break: lower `position` goes first; other shifts by +1
- Delete×Delete same index: both become no-op
- `VertexOpService` loads geometry, extracts exterior ring, applies transformed op, validates via `polygon_from_lonlat`, persists, and records audit
- `RedisVertexOpStore` uses a Lua CAS script (`_LUA_APPEND_IF_REV_MATCHES`) to atomically increment rev and append op; retries on `-1`
- Idle feature OT state expires after `DEFAULT_TTL_SECONDS` (3600) in Redis
- `_build_op_event` constructs `vertex_op_applied` payloads with op-specific metadata

## Touches
| resource | how | why |
|---|---|---|
| services/backend/modules/websocket_runtime.md | `ws_manager.broadcast_ephemeral` | Push `vertex_op_applied` to subscribers |
| services/backend/modules/redis_core.md | Redis sorted set / counter | Multi-worker OT state sharing |
| services/backend/modules/entity_broadcast_audit.md | `AuditService.record` | Audit trail for geometry edits |

## Gotchas
- Single-worker deployments must use `InMemoryVertexOpStore`; multi-worker without Redis silently corrupts geometry (audit C1)
- `base_rev` gap larger than `max_ops` (default 50) forces client reload
- Geometry revision gate (`expected_geom_rev`) rejects vertex ops that target an older polygon shape changed by a concurrent PATCH/cut
- `apply_op` raises `ValueError` if delete would drop below 3 vertices
- `polygon_from_lonlat` catches self-intersections and < 3 vertices after apply
- Audit geometry changes are summarised as `"<vertex edit>" → "move: vertex N"` rather than full coordinate diffs
