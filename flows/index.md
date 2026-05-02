---
---

# Cross-service Flows

End-to-end sequences spanning multiple services.

| Flow | Trigger | Services |
|---|---|---|

Frontend-only user journeys are documented in [services/ui/index.md](../services/ui/index.md).

## Cross-service end-to-end flows

| Flow | Trigger | Services | Frontend journey | Backend sequence |
|---|---|---|---|---|
| [entity-creation-end-to-end](entity-creation-end-to-end.md) | FAB add action | ui, backend | [entity-creation-on-map](../services/ui/flows/entity-creation-on-map.md) | [entity_creation](../services/backend/flows/entity_creation.md) |
| [entity-update-end-to-end](entity-update-end-to-end.md) | Entity edit save | ui, backend | [entity-edit-session](../services/ui/flows/entity-edit-session.md) | [entity_update](../services/backend/flows/entity_update.md) |
| [planning-cycle-end-to-end](planning-cycle-end-to-end.md) | Planning panel action | ui, backend | [planning-cycle-submission](../services/ui/flows/planning-cycle-submission.md) | [planning_cycle_lifecycle](../services/backend/flows/planning_cycle_lifecycle.md) |
| [clash-detect-end-to-end](clash-detect-end-to-end.md) | Clash panel interaction | ui, backend | [clash-detection-workflow](../services/ui/flows/clash-detection-workflow.md) | [clash_detect_and_resolve](../services/backend/flows/clash_detect_and_resolve.md) |
| [vertex-op-end-to-end](vertex-op-end-to-end.md) | Vertex edit save | ui, backend | [polygon-vertex-edit](../services/ui/flows/polygon-vertex-edit.md) | [vertex_op_flow](../services/backend/flows/vertex_op_flow.md) |
| [report-export-end-to-end](report-export-end-to-end.md) | Report export button | ui, backend | [report-generation-export](../services/ui/flows/report-generation-export.md) | [report_export_flow](../services/backend/flows/report_export_flow.md) |

### Frontend-only flows (no backend sequence pair yet)

| Flow | Trigger |
|---|---|
| [login-to-dashboard](../services/ui/flows/login-to-dashboard.md) | `/login` → OIDC → site selection → dashboard bootstrap |
| [entity-delete-with-undo](../services/ui/flows/entity-delete-with-undo.md) | Delete key/button → confirmation → API → undo record |
| [map-entity-drag](../services/ui/flows/map-entity-drag.md) | Map mouse down on entity → threshold → drag → commit |
| [websocket-reconnection-catchup](../services/ui/flows/websocket-reconnection-catchup.md) | WS connection drop → reconnect → catch-up → offline queue |
| [revision-mode-navigation](../services/ui/flows/revision-mode-navigation.md) | Enter revision mode → snapshot fetch → timeline/compare |
| [site-settings-management](../services/ui/flows/site-settings-management.md) | Site settings modal → shift/contractor/invite/smart-group CRUD |
