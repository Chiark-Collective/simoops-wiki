---
trigger: { channel: ui, ref: "clash panel interaction or entity mutation" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User opens the clash panel or mutates site/shift/date/entity visibility.

## Steps
1. `dashboard/clash-dashboard.component.ts::ClashDashboardComponent` receives `site`, `shift`, `workDate`, `tokens`, `plant`, `areas`, `roads`, `currentMinutes` inputs.
2. `ngOnChanges` detects context change (`site`/`shift`/`workDate`) → `scheduleRefresh` → debounced HTTP fetch via `refreshSubject.pipe(debounceTime(100), switchMap(...))` to `api.service.ts::ApiService.listClashes` over full shift range ([HTTP contract](../contracts/ui-backend/http-contract.md)).
3. `refreshClashes` bypasses debounce for immediate fetch after resolve/unresolve or `clashRefreshRequested$`.
4. Backend `api/routes/clash_routes.py` → `services/clash_detection.py::list_clashes` → `clash_cache.py` lookup by `(site_id, shift_id, generation)`.
5. `clash_cache.get_or_compute` checks cache generation inside `asyncio.Lock`; on miss or stale generation proceeds to recompute.
6. Cache miss or generation mismatch → `clash_engine.py` recomputes per site + shift + time slice.
7. Backend `schedule_recomputation` increments per-site generation, cancels existing debounce timer, starts `_debounced_recompute` after `DEFAULT_RECOMPUTATION_DELAY` (0.5 s).
8. `_load_clash_inputs` loads site, active profile, enabled rules, tokens, plants, clashable features, inactive cranes, and building features; expunges all ORM objects from the session.
9. `_compute_clashes_sync` runs in thread pool via `asyncio.to_thread`: wraps entities with adapters, compiles rules, evaluates via `DeclarativeClashEngine`, formats results with `ClashResultFormatter`, applies same-contractor exemptions.
10. `get_or_compute` loads resolutions, annotates clashes with `resolved` flags, filters unresolved for severity derivation.
11. `derive_entity_severity` computes per-entity worst-case severity from unresolved `ClashRuleResult`s.
12. Backend stores `ClashCacheEntry` (legacy + canonical shapes) in LRU cache.
13. `_debounced_recompute` broadcasts `clash_results_updated` to WebSocket room `site:{site_id}` via `ws_manager` ([backend sequence](../services/backend/flows/clash_detect_and_resolve.md)).
14. Frontend `buildClashLookups` rebuilds id-keyed `ClashEntityLookups` (O(1)) when `tokens`/`plant`/`areas` change.
15. `applyClashResults` filters raw clashes through `hasTimeOverlap` (returns `true` for all inactive crane clashes to avoid synthetic ID collisions).
16. Valid clashes sorted by `clash_type` priority (`crane_crane` highest); `updateVisibleClashesVm` splits active/resolved via `filterByEntityVisibility` against visible entity arrays.
17. `toClashViewModel` pre-computes entity names, icons, and time windows using shared lookups.
18. Outputs emitted: `clashCountChange`, `clashesChange`, `activeClashViewModelsChange`, `resolvedClashViewModelsChange`.
19. `services/clash-interaction.service.ts::ClashInteractionService` absorbs outputs into `services/clash-state.service.ts::ClashStateService` (`setClashes`, `setClashCount`, `setActiveClashViewModels`, `setResolvedClashViewModels`).
20. `ClashStateService.setClashes` is a no-op while `revisionMode.enabled` is true ⟂ live data overwrites historical snapshot.
21. `ClashInteractionService.updateVisibleClashes` calls `ClashStateService.updateVisibleClashes` with `FilteredEntityCacheService` tokens/plants/areas.
22. `ClashInteractionService.updateSelectedClashVms` filters `_activeClashViewModels` by `SelectionService.multiSelectedIds`; resolved clashes excluded.
23. Click: `onClashClicked` → `getClashEntityPositions` computes midpoint → `MapComponent.centerOnPoint`.
24. Double-click: `onClashDoubleClicked` → `getClashEntities` → `SelectionService.selectMultiple` + `BuildingFocusService.selectWithBuildingContext` (roads omitted, no `SpatialEntity` converter).
25. Resolve/unresolve: `ClashInteractionService.resolveClash` / `resolveAllClashesForEntity` → HTTP POST → backend `clash_resolution_service.py::resolve_clash` → DB insert resolution.
26. `entity_broadcast.py` WS broadcast `clash_resolution` to site room ([WebSocket contract](../contracts/ui-backend/websocket-contract.md)).
27. Frontend `ClashResolutionSyncBinding` receives `clash_resolution` → optimistic flip via `wsApplyClashResolved` / `wsApplyClashUnresolved`.
28. Debounced `clashResults$` recompute is authoritative; overrides optimistic state after ~500ms.
29. `services/clash-rule.service.ts::ClashRuleService` loads rules via HTTP; `selectRule` fetches `selectedRuleHistory$` and `selectedRuleDsl$` in parallel; `ruleMutated$` emits on CRUD.
30. `services/rule-profile.service.ts::RuleProfileService.loadProfiles` sets active profile via fallback chain: site-specific active → system active → "Standard" system profile → null.
31. `activateProfile` deactivates others in same site scope; `cloneAndActivate` copies system profile then activates.
32. `services/clash-rule-sync-binding.service.ts::ClashRuleSyncBinding` routes `config_sync` `clash_rule` and `rule_profile` into `ClashRuleService` and `RuleProfileService`.
33. Backend `rule_profile_service.py` / `rule_version_service.py` manage rule profiles.

## Side effects
- HTTP GET `listClashes` (full shift range, cached).
- HTTP POST `resolveClash`, `resolveClashBulk`; DELETE `unresolveClash`.
- HTTP GET/POST/PATCH/DELETE for `clashRules`, `ruleProfiles`.
- WebSocket `clash_results_updated` inbound pushes recomputed clashes directly to `applyClashResults`.
- WebSocket `clash_resolution` inbound optimistic update.
- WebSocket `config_sync` outbound/inbound for `clash_rule`, `rule_profile`, `clash_resolution`.
- PostGIS reads and in-memory cache write (`ClashCache._cache`).
- Audit log entry for manual rule evaluations.
- `EntitySeverityService.updateFromClashes` mutates map entity coloring.
- `SelectionService.selectMultiple` mutates global selection.
- `BuildingFocusService.selectWithBuildingContext` mutates floor focus.

## Failure modes
- `listClashes` 404 → empty clash list emitted, count zeroed.
- Cache generation mismatch → stale results served until recompute completes.
- Debounced `switchMap` cancels in-flight HTTP; rapid mutations never pile up.
- `ClashStateService.setClashes` no-op in revision mode → stale live clashes suppressed.
- `ClashResolutionSyncBinding` optimistic resolve may temporarily mismatch authoritative `clashResults$` recompute (debounced ~500ms).
- `hasTimeOverlap` bypass for inactive crane clashes can mask schedule-copy ID collisions.
- Large sites trigger expensive recalculations on every entity mutation.
- Recompute failure → logged; pending task cleaned up; clashes remain stale.
- Rule compilation error → logged; rule skipped; evaluation continues.
- `getClashEntities` omits roads (no `SpatialEntity` converter), so double-click on `token_road` selects only the token.
