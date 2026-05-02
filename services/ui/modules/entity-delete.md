---
service: ui
summary: Delete orchestration, schedule-aware confirmation, bulk ops, and modal result handlers.
paths:
  - src/app/services/entity-delete-orchestrator.service.ts
  - src/app/services/entity-bulk-ops.service.ts
  - src/app/services/modal-result-bulk-ops.service.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Handles entity deletion with schedule-group awareness, confirmation dialogs, undo recording, and multi-select batch operations. `EntityDeleteOrchestrator` routes single and bulk deletes through the per-kind handler table while respecting revision mode, data locks, and planning cycle scope. `EntityBulkOpsService` provides broader bulk operations including clear-all and properties-panel routing.

## Interface
- `services/entity-delete-orchestrator.service.ts::EntityDeleteOrchestrator` — Schedule-aware confirmed delete for workers, plants, and areas; single-item, multi-select, active feature, and building deletion; undo recording and selection cleanup.
- `services/entity-delete-orchestrator.service.ts::BatchDeleteResult` — Per-entity outcome type for batch deletes.
- `services/entity-bulk-ops.service.ts::EntityBulkOpsService` — Bulk lock/unlock, clear-all per entity type, properties panel field edits, floor selection, and delete routing.
- `services/modal-result-bulk-ops.service.ts::ModalResultBulkOpsHandler` — Listens for copy, bulk import, bulk edit, and wipe modal results and reloads affected entity types.
