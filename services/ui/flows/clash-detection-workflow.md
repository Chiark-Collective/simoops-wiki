---
trigger: { channel: ui, ref: "clash panel interaction" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User opens the clash panel or mutates site/shift/date/entity visibility.

## Steps
1. `dashboard/clash-dashboard.component.ts::ClashDashboardComponent` receives `site`, `shift`, `workDate`, `tokens`, `plant`, `areas`, `roads`, `currentMinutes` inputs.
2. `ngOnChanges` detects context change (`site`/`shift`/`workDate`) → `scheduleRefresh` → debounced HTTP fetch via `refreshSubject.pipe(debounceTime(100), switchMap(...))` to `api.service.ts::ApiService.listClashes` over full shift range.
3. `refreshClashes` bypasses debounce for immediate fetch (called after resolve/unresolve or `clashRefreshRequested$`).
4. `buildClashLookups` rebuilds id-keyed `ClashEntityLookups` (O(1)) when `tokens`/`plant`/`areas` change.
5. `applyClashResults` filters raw clashes through `hasTimeOverlap` (returns `true` for all inactive crane clashes to avoid synthetic ID collisions).
6. Valid clashes sorted by `clash_type` priority (`crane_crane` highest).
7. `updateVisibleClashesVm` splits into active/resolved via `filterByEntityVisibility` against visible entity arrays.
8. `toClashViewModel` pre-computes entity names, icons, and time windows using shared lookups.
9. Outputs emitted: `clashCountChange`, `clashesChange`, `activeClashViewModelsChange`, `resolvedClashViewModelsChange`.
10. `services/clash-interaction.service.ts::ClashInteractionService` absorbs outputs into `services/clash-state.service.ts::ClashStateService` (`setClashes`, `setClashCount`, `setActiveClashViewModels`, `setResolvedClashViewModels`).
11. `ClashStateService.setClashes` is a no-op while `revisionMode.enabled` is true ⟂ live data overwrites historical snapshot.
12. `ClashInteractionService.updateVisibleClashes` calls `ClashStateService.updateVisibleClashes` with `FilteredEntityCacheService` tokens/plants/areas.
13. `ClashInteractionService.updateSelectedClashVms` filters `_activeClashViewModels` by `SelectionService.multiSelectedIds`; resolved clashes excluded.
14. Click: `onClashClicked` → `getClashEntityPositions` computes midpoint → `MapComponent.centerOnPoint`.
15. Double-click: `onClashDoubleClicked` → `getClashEntities` → `SelectionService.selectMultiple` + `BuildingFocusService.selectWithBuildingContext` (roads omitted, no `SpatialEntity` converter).
16. Resolve/unresolve: `onNoticeboardResolveClash` / `onNoticeboardUnresolveClash` / `resolveAllClashesForEntity` → HTTP → `requestClashRefresh`.
17. `services/clash-rule.service.ts::ClashRuleService` loads rules via HTTP; `selectRule` fetches `selectedRuleHistory$` and `selectedRuleDsl$` in parallel; `ruleMutated$` emits on CRUD.
18. `services/rule-profile.service.ts::RuleProfileService.loadProfiles` sets active profile via fallback chain: site-specific active → system active → "Standard" system profile → null.
19. `activateProfile` deactivates others in same site scope; `cloneAndActivate` copies system profile then activates.
20. WebSocket `clashResults$` pushes recomputed clashes directly to `applyClashResults`.
21. `services/clash-rule-sync-binding.service.ts::ClashRuleSyncBinding` routes `config_sync` `clash_rule` and `rule_profile` into `ClashRuleService` and `RuleProfileService`.
22. `services/clash-resolution-sync-binding.service.ts::ClashResolutionSyncBinding` routes `config_sync` `clash_resolution` into `ClashStateService.wsApplyClashResolved` / `wsApplyClashUnresolved`.

## Side effects
- HTTP GET `listClashes` (full shift range, cached).
- HTTP POST `resolveClash`, `resolveClashBulk`; DELETE `unresolveClash`.
- HTTP GET/POST/PATCH/DELETE for `clashRules`, `ruleProfiles`.
- WebSocket `clashResults$` inbound (pushed recomputed clashes).
- WebSocket `config_sync` outbound/inbound for `clash_rule`, `rule_profile`, `clash_resolution`.
- `EntitySeverityService.updateFromClashes` mutates map entity coloring.
- `SelectionService.selectMultiple` mutates global selection.
- `BuildingFocusService.selectWithBuildingContext` mutates floor focus.

## Failure modes
- `listClashes` 404 → empty clash list emitted, count zeroed.
- Debounced `switchMap` cancels in-flight HTTP; rapid mutations never pile up.
- `ClashStateService.setClashes` no-op in revision mode → stale live clashes suppressed.
- `ClashResolutionSyncBinding` optimistic resolve may temporarily mismatch authoritative `clashResults$` recompute (debounced ~500ms).
- `hasTimeOverlap` bypass for inactive crane clashes can mask real schedule-copy ID collisions.
- `getClashEntities` omits roads (no `SpatialEntity` converter), so double-click on `token_road` selects only the token.
