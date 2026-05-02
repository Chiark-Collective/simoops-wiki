---
service: ui
summary: Report session lifecycle, scene capture, template management, and export.
paths:
  - services/report-orchestrator.service.ts
  - services/report-session.service.ts
  - services/report-session-sync-binding.service.ts
  - api/report.api.ts
  - dashboard/report-panel/
  - components/report-wizard/
  - types/report.types.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Orchestrates report generation workflows: scene selection on the map, session creation/autosave, template-based report building, and PDF/DOCX export. Syncs report session state via WebSocket.

## Interface
- `services/report-orchestrator.service.ts::ReportOrchestrator` — Scene overlay management (`MapSceneOverlay`), custom bounds drawing, scene capture with minimap compositing, and export coordination.
- `services/report-session.service.ts::ReportSessionService` — Report session state (picker, form, autosave), sticky defaults, delivery integration, and export request building. Emits `saveStatus$` (`saved` | `saving` | `unsaved` | `error`).
- `services/report-session.service.ts::ReportWizardView` — `'picker'` | `'form'`.
- `services/report-session.service.ts::ReportSaveStatus` — `'saved'` | `'saving'` | `'unsaved'` | `'error'`.
- `services/report-session.service.ts::ReportExportRequest` — `{ sessionId, format, displayOptions }`.
- `services/report-session-sync-binding.service.ts::ReportSessionSyncBindingService` — Bridges WebSocket report events into `ReportSessionService`.
- `api/report.api.ts::ReportApi` — HTTP wrapper for report templates, sessions, and export endpoints.
- `dashboard/report-panel/report-panel.component.ts::ReportPanelComponent` — Thin presenter for report session UI.
- `components/report-wizard/report-wizard.component.ts::ReportWizardComponent` — Wizard for report creation flow.
- `types/report.types.ts` — `ReportTemplate`, `ReportSession`, `ReportScene`, `SceneDisplayOptions`, `CustomOverviewBounds`, etc.
