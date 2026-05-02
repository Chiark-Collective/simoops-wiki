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
touches:
  - localStorage
  - HTTP
  - WebSocket
external: []
last_verified_commit: cf53fca56d8d8f023b3d434223b7a050c61b918b
---

## Purpose
Manages the current working site context and all site-level administration: contractor/shift/invite/smart-group CRUD, layer rules, label styles, and site settings. Syncs site-level data via WebSocket bindings.

## Interface
- `services/site-context.service.ts::SiteContextService` — streams for sites, selected site, shifts, contractors, site maps, site configs. Emits `WorkingContext` when site + shift are valid. Auto-restores last site from `localStorage`.
- `services/site-context.service.ts::WorkingContext` — `{ site, shift, date, siteMap? }`.
- `services/site-configuration.service.ts::SiteConfigurationService` — facade re-exporting `SiteScheduleService`, `InviteService`, `LayerRulesService`. Orchestrates settings modal lifecycle and permission-gated data loading.
- `services/site-configuration.service.ts::SiteConfigResult` — `{ success, message, data? }`.
- `services/site-schedule.service.ts::SiteScheduleService` — shift schedule cache (`siteConfigs`) and editing config (`editingSiteConfig`). Form helpers and prepare/save logic.
- `services/invite.service.ts::InviteService` — invite, invite-link, and pending-member state with CRUD and idempotent WS apply methods.
- `services/smart-group.service.ts::SmartGroupService` — smart group CRUD, activation, ad-hoc filtering, client-side evaluation via `SelectionFilterService`.
- `services/layer-rules.service.ts::LayerRulesService` — `layerRules` and `layerDefaultsData` state loaded on demand for the settings modal.
- `services/layer-defaults.service.ts::LayerDefaultsService` — `canDrag`, `canDelete`, `canHaveCuts`, `isExclusive` based on per-type defaults.
- `services/label-style.service.ts::LabelStyleService` — per-site label style cache with fallback to `LABEL_STYLE_DEFAULTS`.
- `services/contractor-visibility.service.ts::ContractorVisibilityService` — hidden-contractor set, entity visibility check, per-contractor counts.
- `services/config-sync.service.ts::ConfigSyncService` — routes `config_changed` WS events to per-domain handlers.
- `services/contractor-sync-binding.service.ts::ContractorSyncBinding` — registers `contractor` domain handler → `SiteContextService.wsApplyContractor*`.
- `services/shift-sync-binding.service.ts::ShiftSyncBinding` — registers `shift` domain handler → `SiteContextService.wsApplyShift*`.
- `services/invite-sync-binding.service.ts::InviteSyncBinding` — registers `invite`, `invite_link`, `membership` domain handlers → `InviteService.wsApply*`.
- `services/smart-group-sync-binding.service.ts::SmartGroupSyncBinding` — registers `smart_group` domain handler → `SmartGroupService.wsApplySmartGroup*`.
- `services/site-map-sync-binding.service.ts::SiteMapSyncBinding` — registers `site_map` domain handler → `SiteContextService.wsApplySiteMap*`.
- `services/label-style-sync-binding.service.ts::LabelStyleSyncBinding` — registers `label_style` domain handler → `LabelStyleService.wsApplyStyles`.
- `dashboard/site-settings-host/` — `SiteSettingsHostComponent`: modal event wiring, shift/contractor/invite CRUD, site visibility/elevation/planning updates.
- `dashboard/panels/contractor-panel/` — `ContractorPanelComponent`: per-contractor visibility toggles, search, counts.
- `dashboard/panels/layers-panel/` — `LayersPanelComponent`: layer visibility toggles and counts by entity type.
- `types/smart-group.types.ts` — `SmartGroup`, `SmartGroupQuery`, `SmartGroupCreatePayload`, `SmartGroupEvaluationResult`, `AggregateStatistics`.

## State
- `SiteContextService` maintains `_sites`, `_selectedSite`, `_shifts`, `_contractors`, `_siteMaps`, `_selectedSiteMap`, `_siteConfigs`. Selected date and shift are delegated to `TemporalContextService`. Invariant: `site selected ⟂ _shifts` must be for that site; `selectSite` resets them atomically.
- `SiteScheduleService` maintains `_siteConfigs` (cached `ShiftSchedule[]` per site) and `_editingSiteConfig` (draft for modal). `_editingSiteConfig` is replaced immutably to trigger subscribers.
- `InviteService` maintains `_invites`, `_inviteLinks`, `_pendingMembers`, `_isLoadingInvites`. Revoked invites remain in `_invites` with status `revoked`; deleted invite links are removed from `_inviteLinks`.
- `SmartGroupService` maintains `_groups`, `_activeGroup`, `_activeAdHocFilter`, `_matchedIds`, `_statistics`, `_evaluating`. Only one filter slot may be active at a time (`_activeGroup` or `_activeAdHocFilter`, never both).
- `LayerRulesService` maintains `_layerRules`, `_layerDefaultsData`, `_isLoadingLayerRules`. Loaded on demand.
- `LabelStyleService` maintains `_styles` as a site-scoped collection; falls back to `LABEL_STYLE_DEFAULTS` on load failure.
- `LayerDefaultsService` maintains `_defaults` with site-id caching to avoid redundant fetches.
- `ContractorVisibilityService` maintains `_hiddenContractorIds`, `_cachedContractorCounts`, `_colorMap`. `_hiddenContractorIds` resets to empty `Set` on site change.

## Internals
- Site context restoration: `tryRestoreSite` reads `localStorage` key `simoops_last_site_id` → matches against loaded `_sites` → calls `selectSite`. `getLastSelectedSiteId` is for UI pre-focus only.
- Working context emission: `combineLatest([_selectedSite, temporalContext.selectedShift$, temporalContext.selectedDate$, _selectedSiteMap])` → `map` to `WorkingContext | null` when site and shift exist. `distinctUntilChanged` compares site id, shift id, date, and site map id.
- Site selection cascade: `selectSite(site)` → `_selectedSite.next(site)` → `timezone.setSiteTz` → `temporalContext.setSelectedShift(null)` → reset shifts/contractors/maps → `UserService.setActiveSite` → `localStorage.setItem` → `temporalContext.setSelectedDate(siteToday)` → `loadShifts`, `loadContractors`, `loadSiteMaps`.
- Shift auto-selection: `loadShifts` finds the shift covering current site-local minutes (handles overnight shifts where `startMinutes >= endMinutes`). If no match, selects `shifts[0]`.
- Site map auto-selection: `loadSiteMaps` selects the first map with `status === 'ready'`; non-ready maps (processing uploads) are skipped to avoid blank tiles.
- Configuration facade: `SiteConfigurationService` re-exports observables/getters/setters from sub-services. Orchestration methods gate invite loading on `UserService.isCoordinatorOrAbove()`.
- Sync binding pattern: each `*SyncBinding` injects `ConfigSyncService` and calls `register(domain, handler)` in its constructor. Handlers are idempotent (upsert/no-op on missing) so catch-up replay after WS reconnection is safe. `ConfigSyncService.dispatch` catches handler errors to prevent one domain from breaking others.
- Layer defaults evaluation: `LayerDefaultsService.getEffectiveType` resolves `feature_type` > infer `building` from non-empty `levels` > `'unknown'`. `canDrag` returns `!defaults.fixed`; `canDelete` returns `defaults.deleteable`; no defaults → allow.
- Smart group evaluation: client-side only. `activateGroup` / `activateAdHocFilter` call `SelectionFilterService.evaluateQuery` against currently visible entities, then publish `_matchedIds` and `_statistics`. Backend `/evaluate` is a stub.
- Shift save flow: `SiteSettingsHostComponent.saveSiteConfig` → `SiteScheduleService.prepareSaveSiteConfig` filters out shifts that already have IDs → API `createShift` for each new shift → `SiteScheduleService.addShiftToConfig` with the returned ID.

## Touches
- `localStorage` — `simoops_last_site_id` for cross-session site restoration.
- `HTTP` — all CRUD via `ApiService` (sites, shifts, contractors, invites, smart groups, layer rules, label styles, site maps).
- `WebSocket` — `ConfigSyncService` subscribes to `WebSocketService.events$` and routes `config_changed` broadcasts to domain handlers.

## Gotchas
- `SiteContextService.selectedShift$` and `selectedDate$` are getters returning `TemporalContextService` observables. Binding directly in templates creates a new reference each CD cycle; cache in a component property or use `siteContext.context$`.
- `SiteContextService.selectSite` resets shift/contractor/map state and updates `UserService.activeSite`. Downstream consumers relying on stale contractor IDs after a site switch see empty arrays until loads complete.
- `ContractorSyncBinding`, `ShiftSyncBinding`, etc. must be injected eagerly (e.g., by `DashboardComponent`) before the first WS broadcast arrives; lazy injection misses early events.
- `InviteService.wsApplyInviteDeleted` flips status to `revoked` rather than removing the row because the backend soft-deletes invites.
- `SmartGroupService.wsApplySmartGroupUpdated` treats an update for an unknown row as a create — this handles the sharing-transition case where a non-owner client did not previously have the group.
- `SiteSettingsHostComponent` uses `OnPush` and calls `cdr.markForCheck()` on invite/pending-member/link changes because the template reads synchronous getters, not async pipes.
- `SiteScheduleService.prepareSaveSiteConfig` returns only new shifts (those without IDs). The caller must persist each via API and then call `addShiftToConfig` to inject the returned ID into the cache; until then the timeline lacks that shift.
- `LayerDefaultsService.loadForSite` is a no-op if `currentSiteId === siteId` and defaults are already cached; force a refresh by calling `clear()` first.
