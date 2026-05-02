---
service: ui
summary: Clash detection state, interaction, rules, and profile management.
paths:
  - services/clash-state.service.ts
  - services/clash-interaction.service.ts
  - services/clash-hover.service.ts
  - services/clash-rule.service.ts
  - services/clash-rule-sync-binding.service.ts
  - services/clash-resolution-sync-binding.service.ts
  - services/rule-profile.service.ts
  - dashboard/clash-dashboard.component.ts
  - dashboard/clash-hover-tooltip.component.ts
  - types/clash-rule.types.ts
flows: []
touches: []
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Centralized clash detection UI state: absorbs raw clash data from API/WebSocket, computes view models, handles filtering/selection/resolution, and manages clash rules with versioning and profiles.

## Interface
- `services/clash-state.service.ts::ClashStateService` — `BehaviorSubject`-driven store for clashes, clash count, active/resolved view models, visible clashes, and selected clashes. Integrates with `RevisionModeService` to swap live data for historical snapshots.
- `services/clash-interaction.service.ts::ClashInteractionService` — Handles clash click, resolve/unresolve, multi-select filtering, and map centering. Registers `MapComponent` reference for spatial operations.
- `services/clash-hover.service.ts::ClashHoverService` — Tracks hovered clash and derived entity/tooltip state.
- `services/clash-rule.service.ts::ClashRuleService` — CRUD for clash rules, version history (`selectedRuleHistory$`), DSL generation (`selectedRuleDsl$`), and rule mutation events (`ruleMutated$`).
- `services/clash-rule-sync-binding.service.ts::ClashRuleSyncBindingService` — Bridges WebSocket rule events into `ClashRuleService` state.
- `services/clash-resolution-sync-binding.service.ts::ClashResolutionSyncBindingService` — Bridges WebSocket resolution events into clash state.
- `services/rule-profile.service.ts::RuleProfileService` — CRUD for rule profiles (activation, cloning, templates).
- `dashboard/clash-dashboard.component.ts::ClashDashboardComponent` — Main clash panel; fetches clashes and pushes into `ClashStateService`.
- `dashboard/clash-hover-tooltip.component.ts::ClashHoverTooltipComponent` — Tooltip for hovered clash entities on the map.
- `types/clash-rule.types.ts` — `ClashRule`, `ClashRuleCreatePayload`, `ClashRuleUpdatePayload`, `ClashRuleVersion`, `RuleProfile`, etc.
