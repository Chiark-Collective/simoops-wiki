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
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Real-time synchronization layer: WebSocket connection management with room subscriptions and sequence tracking for incremental catch-up, event routing to domain services, presence tracking, offline operation queuing, and undo support.

## Interface
- `services/websocket.service.ts::WebSocketService` — Room subscribe/unsubscribe, per-room sequence tracking (`lastReceivedSeq`), catch-up after reconnection, entity broadcast sending, and ephemeral position publishing. Exposes `connectionState$`, `events$`, `entityEvents$`, `presenceEvents$`.
- `services/websocket-event-router.service.ts::WebSocketEventRouterService` — Routes incoming `WebSocketEntityEvent` to `EntityService`, `DeliveryService`, `PoiService`, `AlertService`, `TextLabelService`, `GeometadataService`, `SelectionService`, `UndoService`, `RoadEditorStateService`, and `RevisionModeService`. Breaks circular dependency between WebSocket and domain services.
- `services/websocket-connection.ts::WebSocketConnection` — Low-level WebSocket wrapper: connect, reconnect with exponential backoff, heartbeat, message serialization.
- `services/websocket.types.ts` — `ConnectionState`, `WebSocketEntityEvent`, `WebSocketBroadcastEvent`, `ClashResultsEvent`, `CatchUpResponseEvent`, `EphemeralPositionEvent`, `VertexOpEvent`, `PresenceEvent`, etc.
- `services/presence.service.ts::PresenceService` — Presence tracking: local viewport publishing, remote viewport display, user list.
- `services/offline-queue.service.ts::OfflineQueueService` — Queues operations while offline and replays on reconnection.
- `services/data-lock.service.ts::DataLockService` — Data lock acquisition and release for optimistic concurrency.
- `services/undo.service.ts::UndoService` — Undo/redo stack for entity operations.
- `services/search-state.service.ts::SearchStateService` — Global search query state.
- `services/search-filter.service.ts::SearchFilterService` — Search result filtering.
- `services/message.service.ts::MessageService` — User notification toasts and messages.
- `services/modal.service.ts::ModalService` — Modal open/close orchestration.
- `services/console-log.service.ts::ConsoleLogService` — Structured console logging initialization.
