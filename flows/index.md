---
---

# Cross-service Flows

End-to-end sequences spanning multiple services.

| Flow | Trigger | Services |
|---|---|---|

Frontend-only user journeys are documented in [services/ui/index.md](../services/ui/index.md).

Cross-service end-to-end flows (combining frontend triggers with backend sequences) are pending. Candidate pairs:

| Frontend flow | Backend flow | Cross-service opportunity |
|---|---|---|
| [login-to-dashboard](../services/ui/flows/login-to-dashboard.md) | — | OIDC token exchange → site context cascade |
| [entity-creation-on-map](../services/ui/flows/entity-creation-on-map.md) | [entity_creation](../services/backend/flows/entity_creation.md) | FAB → API → broadcast → map refresh |
| [entity-edit-session](../services/ui/flows/entity-edit-session.md) | [entity_update](../services/backend/flows/entity_update.md) | Modal → PATCH → audit → WS merge |
| [entity-delete-with-undo](../services/ui/flows/entity-delete-with-undo.md) | — | Delete → undo stack → selection cleanup |
| [map-entity-drag](../services/ui/flows/map-entity-drag.md) | — | Drag → ephemeral WS → HTTP commit → source update |
| [websocket-reconnection-catchup](../services/ui/flows/websocket-reconnection-catchup.md) | — | Drop → reconnect → catch-up → offline queue |
| [planning-cycle-submission](../services/ui/flows/planning-cycle-submission.md) | [planning_cycle_lifecycle](../services/backend/flows/planning_cycle_lifecycle.md) | Panel → cycle CRUD → submission → actualize |
| [revision-mode-navigation](../services/ui/flows/revision-mode-navigation.md) | — | Enter → snapshot fetch → compare → exit |
| [report-generation-export](../services/ui/flows/report-generation-export.md) | [report_export_flow](../services/backend/flows/report_export_flow.md) | Scene selection → capture → export pipeline |
| [clash-detection-workflow](../services/ui/flows/clash-detection-workflow.md) | [clash_detect_and_resolve](../services/backend/flows/clash_detect_and_resolve.md) | Panel → fetch → resolve → WS recompute |
| [polygon-vertex-edit](../services/ui/flows/polygon-vertex-edit.md) | [vertex_op_flow](../services/backend/flows/vertex_op_flow.md) | Vertex edit → OT op → broadcast → remote apply |
| [site-settings-management](../services/ui/flows/site-settings-management.md) | — | Modal → CRUD → WS config_sync broadcast |
