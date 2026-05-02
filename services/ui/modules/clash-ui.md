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
flows:
  - API/WebSocket → clash-dashboard.component.ts → outputs → ClashInteractionService → ClashStateService → consumers
  - API → ClashRuleService → rule list / editor
  - API → RuleProfileService → profile selector
  - WebSocket clash_resolution → ClashResolutionSyncBinding → ClashStateService
  - WebSocket clash_rule / rule_profile → ClashRuleSyncBinding → ClashRuleService / RuleProfileService
touches:
  - HTTP: listClashes, resolveClash, resolveClashBulk, unresolveClash, listClashRules, getClashRule, createClashRule, updateClashRule, deleteClashRule, getClashRuleHistory, getClashRuleDsl, getClashRuleVersion, revertClashRule, diffClashRuleVersions, previewClashRuleDsl, listRuleProfiles, getRuleProfile, createRuleProfile, updateRuleProfile, deleteRuleProfile, activateRuleProfile, cloneRuleProfile, listProfileRules
  - WebSocket: clashResults$, config_sync channels clash_rule, rule_profile, clash_resolution
external:
  - services/entity-severity.service.ts::EntitySeverityService
  - services/revision-mode.service.ts::RevisionModeService
  - services/config-sync.service.ts::ConfigSyncService
  - services/websocket.service.ts::WebSocketService
  - api.service.ts::ApiService
  - services/time-utility.service.ts::TimeUtilityService
  - services/entity.service.ts::EntityService
  - services/site-context.service.ts::SiteContextService
  - services/filtered-entity-cache.service.ts::FilteredEntityCacheService
  - services/road-editor-state.service.ts::RoadEditorStateService
  - services/selection.service.ts::SelectionService
  - services/building-focus.service.ts::BuildingFocusService
  - map/map.component.ts::MapComponent
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Centralized clash detection UI state: absorbs raw clash data from API/WebSocket, computes view models, handles filtering/selection/resolution, and manages clash rules with versioning and profiles.

## Interface
- `services/clash-state.service.ts::ClashStateService` — `BehaviorSubject`-driven store for clashes, clash count, active/resolved view models, visible clashes, and selected clashes. Integrates with `RevisionModeService` to swap live data for historical snapshots.
- `services/clash-interaction.service.ts::ClashInteractionService` — Handles clash click, resolve/unresolve, multi-select filtering, and map centering. Registers `MapComponent` reference for spatial operations.
- `services/clash-hover.service.ts::ClashHoverService` — Tracks hovered clash and derived entity/tooltip state.
- `services/clash-rule.service.ts::ClashRuleService` — CRUD for clash rules, version history (`selectedRuleHistory$`), DSL generation (`selectedRuleDsl$`), and rule mutation events (`ruleMutated$`).
- `services/clash-rule-sync-binding.service.ts::ClashRuleSyncBinding` — Bridges WebSocket rule events into `ClashRuleService` state.
- `services/clash-resolution-sync-binding.service.ts::ClashResolutionSyncBinding` — Bridges WebSocket resolution events into clash state.
- `services/rule-profile.service.ts::RuleProfileService` — CRUD for rule profiles (activation, cloning, templates).
- `dashboard/clash-dashboard.component.ts::ClashDashboardComponent` — Main clash panel; fetches clashes and emits view-model outputs wired into `ClashStateService`.
- `dashboard/clash-hover-tooltip.component.ts::ClashHoverTooltipComponent` — Tooltip for hovered clash entities on the map.
- `types/clash-rule.types.ts` — `ClashRule`, `ClashRuleCreatePayload`, `ClashRuleUpdatePayload`, `ClashRuleVersion`, `RuleProfile`, etc.

## State
- `services/clash-state.service.ts::ClashStateService` — `_clashes`, `_clashCount`, `_activeClashViewModels`, `_resolvedClashViewModels`, `_visibleClashes`, `_selectedClashVms`, `_clashRefreshRequested`.
- `services/clash-hover.service.ts::ClashHoverService` — `_hoveredClash`.
- `services/clash-rule.service.ts::ClashRuleService` — `_rules`, `_loading`, `_selectedRule`, `_selectedRuleHistory`, `_selectedRuleDsl`, `_ruleMutated`.
- `services/rule-profile.service.ts::RuleProfileService` — `_profiles`, `_loading`, `_activeProfile`, `_activeProfileSource`, `_selectedProfile`.

## Internals
`dashboard/clash-dashboard.component.ts::ClashDashboardComponent` builds id-keyed `ClashEntityLookups` via `buildClashLookups` (O(1) lookups). `toClashViewModel` pre-computes entity names, icons, time windows. `filterByEntityVisibility` filters by visible tokens/plants/areas/roads. `hasTimeOverlap` filters by temporal overlap (inactive crane clashes bypass). Results sorted by `clash_type` priority (crane_crane highest). `scheduleRefresh` debounces HTTP fetches at 100 ms with `switchMap` cancellation; `refreshClashes` bypasses debounce.

`services/clash-interaction.service.ts::ClashInteractionService` computes entity-position midpoints for map centering. `onClashDoubleClicked` selects involved entities via `SelectionService` and focuses building floor via `BuildingFocusService`. `getClashEntityPositions` handles token, plant, area centroid, road midpoint lookups. `getClashEntities` returns `SpatialEntity` wrappers (roads excluded). Resolve/unresolve/bulk methods call HTTP endpoints and request a refresh.

`services/clash-rule.service.ts::ClashRuleService` fetches via API, mutates local `_rules`, and emits `ruleMutated$`. `selectRule` fetches history and DSL in parallel. `getDsl` and `previewDsl` return `DslGenerationResponse`. `revertToVersion` refreshes `_selectedRuleHistory` if the reverted rule is selected.

`services/rule-profile.service.ts::RuleProfileService` loads profiles with a fallback active-profile chain (site → system → "Standard"). `activateProfile` deactivates others in the same site scope. `cloneAndActivate` copies a system profile and activates it in one step.

`services/clash-rule-sync-binding.service.ts::ClashRuleSyncBinding` registers `ConfigSyncService` handlers for `clash_rule` (created/updated/deleted) and `rule_profile` (created/updated/deleted/activated).

`services/clash-resolution-sync-binding.service.ts::ClashResolutionSyncBinding` registers `clash_resolution` (created/updated → resolve, deleted → unresolve).

## Touches
- HTTP: `listClashes`, `resolveClash`, `resolveClashBulk`, `unresolveClash`, `listClashRules`, `getClashRule`, `createClashRule`, `updateClashRule`, `deleteClashRule`, `getClashRuleHistory`, `getClashRuleDsl`, `getClashRuleVersion`, `revertClashRule`, `diffClashRuleVersions`, `previewClashRuleDsl`, `listRuleProfiles`, `getRuleProfile`, `createRuleProfile`, `updateRuleProfile`, `deleteRuleProfile`, `activateRuleProfile`, `cloneRuleProfile`, `listProfileRules`.
- WebSocket: `clashResults$` (pushed recomputed clashes), `config_sync` channels `clash_rule`, `rule_profile`, `clash_resolution`.

## Gotchas
- `ClashStateService.setClashes` is a no-op while `revisionMode.enabled` is true ⟂ live data overwrites historical snapshot.
- `ClashResolutionSyncBinding` flips the `resolved` flag optimistically; the debounced `clashResults$` recompute is authoritative. Temporary mismatch possible if the backend rejects or recomputes differently.
- `ClashDashboardComponent` queries the full shift range (stable cache key) and filters client-side by `currentMinutes` / entity visibility. `currentMinutes` changes do not trigger HTTP.
- `hasTimeOverlap` returns `true` for all inactive crane clash types because synthetic inactive IDs can collide with schedule copy IDs.
- `getClashEntityPositions` for roads uses the midpoint vertex; roads lack a `SpatialEntity` converter, so `getClashEntities` omits them.
- `ClashRuleSyncBinding` handles both `clash_rule` and `rule_profile` in a single binding because profiles activate sets of rules.
- `RuleProfileService.loadProfiles` sets active profile via fallback chain: site-specific active → system active → "Standard" system profile → null.
- `updateSelectedClashVms` filters `_activeClashViewModels` only; resolved clashes are excluded from multi-selection.
