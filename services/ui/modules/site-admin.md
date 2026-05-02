---
service: ui
summary: Site context, configuration, contractors, shifts, invites, and smart groups.
paths:
  - services/site-context.service.ts
  - services/site-configuration.service.ts
  - services/site-schedule.service.ts
  - services/contractor-sync-binding.service.ts
  - services/contractor-visibility.service.ts
  - services/shift-sync-binding.service.ts
  - services/invite.service.ts
  - services/invite-sync-binding.service.ts
  - services/smart-group.service.ts
  - services/smart-group-sync-binding.service.ts
  - services/site-map-sync-binding.service.ts
  - services/config-sync.service.ts
  - services/label-style.service.ts
  - services/label-style-sync-binding.service.ts
  - services/layer-rules.service.ts
  - services/layer-defaults.service.ts
  - dashboard/site-settings-host/
  - dashboard/panels/contractor-panel/
  - dashboard/panels/layers-panel/
  - types/smart-group.types.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Manages the current working site context and all site-level administration: contractor/shift/invite/smart-group CRUD, layer rules, label styles, and site settings. Syncs site-level data via WebSocket bindings.

## Interface
- `services/site-context.service.ts::SiteContextService` — Observable streams for site, shift, date, contractors, site maps. Emits `WorkingContext` when all selections are valid. Auto-restores last site from `localStorage`.
- `services/site-context.service.ts::WorkingContext` — `{ site, shift, date, siteMap? }`.
- `services/site-configuration.service.ts::SiteConfigurationService` — Facade over `SiteScheduleService`, `InviteService`, and `LayerRulesService`. Orchestrates settings modal, site updates, contractor CRUD, and exemptions.
- `services/site-configuration.service.ts::SiteConfigResult` — `{ success, message, data? }`.
- `services/site-schedule.service.ts::SiteScheduleService` — Shift schedule state, editing config, form helpers.
- `services/invite.service.ts::InviteService` — User invites, invite links, pending members.
- `services/smart-group.service.ts::SmartGroupService` — Smart group CRUD and evaluation.
- `services/layer-rules.service.ts::LayerRulesService` — Layer type rules (`canDrag`, `canDelete`, etc.).
- `services/layer-defaults.service.ts::LayerDefaultsService` — Default values per layer type.
- `services/label-style.service.ts::LabelStyleService` — Text label style management.
- `services/config-sync.service.ts::ConfigSyncBindingService` — WebSocket sync for site configuration changes.
- `services/contractor-sync-binding.service.ts::ContractorSyncBindingService` — WebSocket sync for contractor changes.
- `services/shift-sync-binding.service.ts::ShiftSyncBindingService` — WebSocket sync for shift changes.
- `services/invite-sync-binding.service.ts::InviteSyncBindingService` — WebSocket sync for invite changes.
- `services/smart-group-sync-binding.service.ts::SmartGroupSyncBindingService` — WebSocket sync for smart group changes.
- `services/site-map-sync-binding.service.ts::SiteMapSyncBindingService` — WebSocket sync for site map changes.
- `services/label-style-sync-binding.service.ts::LabelStyleSyncBindingService` — WebSocket sync for label style changes.
- `dashboard/site-settings-host/` — Settings modal host components.
- `types/smart-group.types.ts` — `SmartGroup`, `SmartGroupCreatePayload`, `SmartGroupEvaluationResult`.
