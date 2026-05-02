---
service: ui
summary: WebSocket connection, event routing, presence, offline queue, and undo.
paths:
  - services/websocket.service.ts
  - services/websocket-event-router.service.ts
  - services/websocket-connection.ts
  - services/websocket.types.ts
  - services/presence.service.ts
  - services/offline-queue.service.ts
  - services/data-lock.service.ts
  - services/undo.service.ts
  - services/search-state.service.ts
  - services/search-filter.service.ts
  - services/message.service.ts
  - services/modal.service.ts
  - services/console-log.service.ts
flows: []
touches:
  - browser:WebSocket
  - browser:localStorage
  - browser:console
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Real-time synchronization layer. WebSocket room subscriptions with per-room sequence tracking and incremental catch-up after reconnection. Routes entity events to domain services, tracks user presence, queues offline mutations with OCC conflict resolution, and maintains undo/redo, modal, search, and console-capture state.

## Interface
- `services/websocket.service.ts::WebSocketService` — Room subscribe/unsubscribe, per-room `lastReceivedSeq` tracking, catch-up after reconnection, entity broadcast sending, ephemeral position/radius/arc publishing. Exposes `connectionState$`, `connectionHealth$`, `events$`, `presenceEvents$`, `clashResults$`, `ephemeralPosition$`, `vertexOp$`, `catchUpResponse$`, `fullReloadRequired$`, `contextInvalidated$`, `subscriptionFailed$`.
- `services/websocket-event-router.service.ts::WebSocketEventRouterService` — Routes `WebSocketEntityEvent` to `EntityService`, `DeliveryService`, `PoiService`, `AlertService`, `TextLabelService`, `GeometadataService`, `SelectionService`, `UndoService`, `RoadEditorStateService`, and `RevisionModeService`. Breaks circular dependency between WebSocket and domain services.
- `services/websocket-connection.ts::WebSocketConnection` — Low-level WebSocket wrapper: connect, reconnect with exponential backoff, heartbeat, message serialization. Emits `connectionState$` and `connectionHealth$`.
- `services/websocket.types.ts` — `ConnectionState`, `WebSocketEntityEvent`, `WebSocketBroadcastEvent`, `ClashResultsEvent`, `CatchUpResponseEvent`, `EphemeralPositionEvent`, `VertexOpEvent`, `PresenceEvent`, `UnknownWebSocketEvent`, type guards (`isEntityEvent`, `isBroadcastEvent`, `isPresenceEvent`, `isUnknownEvent`).
- `services/presence.service.ts::PresenceService` — Presence tracking: local viewport publishing, remote viewport display, user list. Exposes `activeUsers$`, `editingEntities$`, `viewportPositions$`.
- `services/offline-queue.service.ts::OfflineQueueService` — Queues operations while offline, replays on reconnection. Deduplicates and merges mutations for the same entity. Surfaces 409 OCC conflicts via `conflicts$`. Exposes `status$`.
- `services/data-lock.service.ts::DataLockService` — Data lock acquisition and release for optimistic concurrency. Reactive `isLockActive$`, `lockBoundary$`, `isViewingLockedTime$`. Admins bypass lock.
- `services/undo.service.ts::UndoService` — Undo/redo stack for entity operations. Max depth 50. Exposes `state$`. Handles stale marking and data-lock awareness.
- `services/search-state.service.ts::SearchStateService` — Global search query state and results. Integrates with `ModalService` for search/select modals.
- `services/search-filter.service.ts::SearchFilterService` — Search result filtering and keyboard navigation. Stateless.
- `services/message.service.ts::MessageService` — User notification toasts and messages. Auto-clears after 5s by default.
- `services/modal.service.ts::ModalService` — Modal open/close orchestration. Single-modal-at-a-time via typed `ModalToken<T>`. Backward-compatible string API.
- `services/console-log.service.ts::ConsoleLogService` — Structured console logging initialization. In-memory ring buffer (10,000 entries). Exposes `window.simoopsLogs`.

## State
- `WebSocketService` maintains `currentRooms` (desired subscriptions), `confirmedRooms` (server-acknowledged), `lastReceivedSeq` (per-room high watermark), `pendingCatchUpRooms`, `pendingCatchUpSnapshot`, `liveSeqsDuringCatchUp` (dedup set for events arriving during catch-up flight), and `pendingEntityEvents` with `flushScheduled` (microtask batching).
- `WebSocketConnection` holds `ws` instance, `reconnectTimer`, `heartbeatTimer`, `reconnectAttempts`, `_missedPongs`, `_lastPongTime`, and `_connectionState` BehaviorSubject.
- `PresenceService` holds `_activeUsers`, `_editingEntities` (entity_id → user), `_viewportPositions`, and `_cachedEditingEntityNames`.
- `OfflineQueueService` holds `queue`, `_deadLetter`, `_conflicts`, `_status`, and `_connected` flag. Queue persisted to `localStorage`.
- `UndoService` holds `undoStack` and `redoStack` (max depth 50), `_state` BehaviorSubject.
- `ModalService` holds `_internal` BehaviorSubject for a single active modal token + context.
- `MessageService` holds `_message` BehaviorSubject and `messageTimeout`.
- `ConsoleLogService` holds `logs` ring buffer (max 10,000), `originalConsole` references, and error/rejection handlers.
- `SearchStateService` holds `searchTerm` and `searchResults`.

Invariants:
- `pendingCatchUpSnapshot` is frozen at `sendCatchUp` time → guarantees missed events with `seq > snapshot` are applied unless already in `liveSeqsDuringCatchUp`.
- `revisionMode.enabled === true` ⟂ `WebSocketEventRouterService` processes live entity events.
- `ModalService` single-modal-at-a-time → only one token active in `_internal`.

## Internals
- Reconnection backoff: base 1s, max 16s, exponential `2^attempts`, cap at 5 attempts. After max attempts, slow polls every 30s. Resets on `manualReconnect()` or browser `online` event.
- Heartbeat: 30s interval ping, force close after 3 unanswered pongs (90s stale threshold). `connectionHealth$` derives from pong age.
- Catch-up protocol: on reconnect, resubscribe all `currentRooms`, then send `catch_up` with `last_seq`. Response replayed events are deduplicated against `pendingCatchUpSnapshot` and `liveSeqsDuringCatchUp`. If server returns `full_reload_required`, emit `fullReloadRequired$`.
- Out-of-order protection: messages with `seq <= lastReceivedSeq` are discarded before routing.
- Entity event batching: rapid consecutive messages collected into `pendingEntityEvents`, flushed in a single `queueMicrotask`. Non-entity messages bypass the buffer.
- Event routing table: `worker` → `EntityService` token ops; `plant` → `EntityService` plant ops; `zone`/`feature` (zone-like) → `EntityService` area ops + `GeometadataService`; `delivery` → `DeliveryService`; `poi` → `PoiService`; `text_label` → `TextLabelService`; `alert` → `AlertService`; `feature` with `feature_type === 'road'` → `RoadEditorStateService`.
- Batch routing accumulates worker/plant creates/updates/deletes into single store emissions; complex types defer to per-event routing.
- Delete side effects: clear multi-selection, typed selection, and mark undo stack stale before calling handler.
- Offline queue deduplication: `create` followed by `delete` = drop both; `update` followed by `update` = merge payloads (later wins); `create` followed by `update` = fold into create payload.
- Offline replay: sequential Promise chain. 409 conflicts moved to `_conflicts` for user resolution (keep server, force local, or merge fields). Failures retried up to 3 times, then dead-lettered.
- Data lock lifecycle: `DataLockService` subscribes to `data_lock_changed` broadcast and updates `SiteContextService`. `UndoService.markDataLocked` walks both stacks and sets `dataLocked` flag based on `end_at` vs boundary.
- Presence heartbeat: 10s interval while connected. Cleared on disconnect or site switch.
- Console capture: patches `console.log/warn/error` and listens to `window` `error` / `unhandledrejection`. Trims buffer at 10,000 entries.

## Touches
| resource | how | why |
|---|---|---|
| browser:WebSocket | connect, send, receive | real-time entity sync and presence |
| browser:localStorage | read/write `simoops_offline_queue`, `simoops_offline_deadletter`, `simoops_offline_conflicts` | survive page reloads during offline periods |
| browser:console | patch `log`/`warn`/`error`, attach `error`/`unhandledrejection` listeners | structured debug capture |
| browser:document | `visibilitychange` listener | reconnect when tab becomes visible |
| browser:window | `online` listener, `window.simoopsLogs` API | reconnect on network recovery, debug access |

## Gotchas
- Catch-up dedup relies on `pendingCatchUpSnapshot` taken at send time. ! If a live broadcast arrives after `sendCatchUp` but before the response, and its seq is higher than the snapshot, the snapshot threshold prevents silent dropping of legitimately missed events. See `websocket.service.ts::sendCatchUp` "C2 regression" comment.
- `liveSeqsDuringCatchUp` only tracks seqs seen while a catch-up is in flight. ! If a catch-up response arrives after the next reconnection, stale bookkeeping is discarded in `handleConnected`.
- `WebSocketEventRouterService` silently drops all live entity events while `revisionMode.enabled` is true. Exiting revision mode requires an explicit `forceRefreshEntities()` to catch up.
- `entity_updated` with no `data` payload (e.g., audit revert broadcast) is skipped to avoid null corruption. The reverting client refreshes naturally; others catch up on next refresh.
- Offline queue `executeMutation` calls `EntityService.addLocal/updateLocal/removeLocal` optimistically. ! If the API succeeds but the WS broadcast is delayed, local state may be temporarily out of sync with the server seq.
- `UndoService` session-scoped: switching site/date/shift must call `clear()` or stale commands remain in the stack.
- `ModalService` enforces single-modal-at-a-time. Opening a new modal implicitly closes the previous one.
- `ConsoleLogService` must be initialized before other services that log during construction, or early logs are lost.
