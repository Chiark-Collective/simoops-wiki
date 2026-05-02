---
trigger: { channel: websocket, ref: "connection drop" }
services: [ui, backend]
contracts: [ui-backend/websocket-contract]
external: []
---

## Trigger
WebSocket connection drops (network loss, server restart, heartbeat timeout, or tab background throttling).

## Steps
1. `services/websocket-connection.ts::WebSocketConnection` detects drop via `onclose`, `onerror`, or 3 unanswered pongs (90s stale threshold) → `connectionHealth$` emits `'stale'`.
2. `WebSocketConnection.scheduleReconnect` applies exponential backoff: 1s, 2s, 4s, 8s, 16s (max 5 fast attempts), then 30s slow polling. Resets on `manualReconnect()` or browser `online` event.
3. On reconnect, `WebSocketConnection.connect` fetches a fresh JWT via `() => auth.token` and opens `wss://host/ws/entities?token=<jwt>`.
4. `WebSocketConnection.handleOpen` resets `reconnectAttempts`, starts heartbeat (30s ping interval), and invokes `callbacks.onConnected`.
5. `services/websocket.service.ts::WebSocketService.handleConnected` clears `confirmedRooms`, `pendingCatchUpSnapshot`, and `liveSeqsDuringCatchUp`, then resubscribes every `currentRooms` entry.
6. Server confirms subscription with `{ status: "subscribed", room, current_seq }`. `WebSocketService.routeMessage` adds the room to `confirmedRooms` and, if the room was in `pendingCatchUpRooms`, invokes `sendCatchUp(siteId)`.
7. `WebSocketService.sendCatchUp` snapshots `lastReceivedSeq.get(room) || 0` into `pendingCatchUpSnapshot`, initialises `liveSeqsDuringCatchUp` as an empty `Set`, and sends `{ action: "catch_up", site_id, last_seq }` to the backend.
8. While the catch-up request is in flight, any live broadcast with a `seq` increments `lastReceivedSeq` and records the seq in `liveSeqsDuringCatchUp` (dedup guard).
9. Backend replies with `catch_up_response`. `WebSocketService.routeMessage` processes each replayed event:
   - Skip if `seq <= pendingCatchUpSnapshot` (already covered before disconnect).
   - Skip if `seq ∈ liveSeqsDuringCatchUp` (already processed via live broadcast during flight).
   - Remaining events are pushed to `pendingEntityEvents` and flushed via `scheduleFlush`.
10. `WebSocketService.scheduleFlush` batches all pending entity events into a single `queueMicrotask`, then calls `services/websocket-event-router.service.ts::WebSocketEventRouterService.routeEntityEventBatch`.
11. `WebSocketEventRouterService.routeEntityEventBatch` accumulates worker/plant creates/updates/deletes into single store emissions (`wsBatchAddTokens`, `wsBatchUpdateTokens`, etc.) and defers complex types (zone, feature, delivery, poi, text_label, alert) to per-event `routeEntityEvent`.
12. Config-domain catch-up events (`config_changed`) flow through `services/config-sync.service.ts::ConfigSyncService.dispatch` to eagerly-injected sync bindings (`ContractorSyncBinding`, `ShiftSyncBinding`, etc.).
13. Simultaneously, `services/offline-queue.service.ts::OfflineQueueService` observes the `connectionState$` transition from disconnected → connected and invokes `replay()`.
14. `OfflineQueueService.replay` drains the queue sequentially via Promise chain. Each mutation calls `ApiService` (create/update/delete), then updates local state via `EntityService.addLocal/updateLocal/removeLocal`. 409 OCC conflicts are moved to `_conflicts`; failures retry up to 3 times, then dead-letter.

## Side effects
- `WebSocketConnection` mutates `_connectionState`, `reconnectAttempts`, `_missedPongs`, `_lastPongTime`.
- `WebSocketService` mutates `confirmedRooms`, `lastReceivedSeq`, `pendingCatchUpRooms`, `pendingCatchUpSnapshot`, `liveSeqsDuringCatchUp`, `pendingEntityEvents`.
- `OfflineQueueService` mutates `queue`, `_deadLetter`, `_conflicts`, `_status`, and writes to `localStorage` (`simoops_offline_queue`, `simoops_offline_deadletter`, `simoops_offline_conflicts`).
- Domain services mutate reactive stores (`EntityService`, `DeliveryService`, `PoiService`, etc.).
- `WebSocketService` emits `catchUpResponse$`, `fullReloadRequired$`, and `events$` (batched).

## Failure modes
- **Catch-up gap too large**: backend returns `status: "full_reload_required"` → `WebSocketService` emits `fullReloadRequired$`; consumer must reload all entities.
- **C2 regression (silent event drop)**: if `pendingCatchUpSnapshot` were not frozen at send time, a live broadcast arriving during catch-up flight would advance `lastReceivedSeq` and cause the response handler to discard legitimately missed events with seq between the old and new high-watermark.
- **Offline queue conflict**: API returns 409 → mutation moved to `_conflicts` for user resolution (keep server, force local, or merge fields).
- **Offline queue drift**: API succeeds but WS broadcast is delayed → `EntityService` local state temporarily diverges from server seq until the broadcast arrives.
- **Lazy sync binding injection**: `ContractorSyncBinding`, `ShiftSyncBinding`, etc. must be injected eagerly (e.g. in `DashboardComponent`) so `ConfigSyncService.register` runs before the first `config_changed` event; lazy injection silently drops early events.
- **Presence heartbeat timeout**: clients that stop sending `presence_heartbeat` disappear from the presence list even if the WS is connected.
