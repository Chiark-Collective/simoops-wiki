---
trigger: { channel: ui, ref: "site settings modal" }
services: [ui, backend]
contracts: [ui-backend/http-contract, ui-backend/websocket-contract]
external: []
---

## Trigger
User opens the site settings modal from the dashboard toolbar.

## Steps
1. `dashboard/site-settings-host/site-settings-host.component.ts::SiteSettingsHostComponent` renders `<app-settings-modal>` bound to `modalService.isVisible$('settings')`.
2. `services/site-configuration.service.ts::SiteConfigurationService.openSiteModal` initializes the shift cache via `services/site-schedule.service.ts::SiteScheduleService.initializeSiteConfig` and clones it into `editingSiteConfig`.
3. `services/site-configuration.service.ts::SiteConfigurationService.loadAllSettingsData` checks `services/user.service.ts::UserService.isCoordinatorOrAbove`; if true it loads invites, invite links, and pending members via `services/invite.service.ts::InviteService`, otherwise clears those caches.
4. `services/site-context.service.ts::SiteContextService.selectSite` resets `_shifts`, `_contractors`, `_siteMaps`, and `_selectedSiteMap`, then triggers `loadShifts`, `loadContractors`, and `loadSiteMaps` for the new site.
5. `services/site-context.service.ts::SiteContextService.loadShifts` fetches shifts and auto-selects the shift covering current site-local minutes; overnight shifts (`startMinutes >= endMinutes`) match if `currentMinutes >= startMinutes || currentMinutes < endMinutes`.
6. `services/site-context.service.ts::SiteContextService.loadSiteMaps` selects the first map with `status === 'ready'`; maps that are still processing are skipped.
7. On site change inside the modal, `dashboard/site-settings-host/site-settings-host.component.ts::SiteSettingsHostComponent.onSelectSiteFromModal` loads layer defaults via `services/layer-defaults.service.ts::LayerDefaultsService.loadForSite`, loads smart groups via `services/smart-group.service.ts::SmartGroupService.loadGroups`, and emits `siteSelected` to the dashboard.
8. Shift creation in the modal calls `services/site-schedule.service.ts::SiteScheduleService.addShiftToEditingConfig`, converting `NewShiftForm` hours/minutes to `startMinutes`/`endMinutes` and appending to the draft.
9. Shift deletion with a backend ID triggers `api.service.ts::ApiService.deleteShift`; on success `services/site-context.service.ts::SiteContextService.removeShiftLocally` and `services/site-schedule.service.ts::SiteScheduleService.removeShiftFromConfig` purge the shift from local caches.
10. `dashboard/site-settings-host/site-settings-host.component.ts::SiteSettingsHostComponent.saveSiteConfig` calls `services/site-schedule.service.ts::SiteScheduleService.prepareSaveSiteConfig`, which returns only new shifts (those lacking an ID).
11. For each new shift the host converts minutes to ISO datetimes and calls `services/site-context.service.ts::SiteContextService.createShift`; on success it injects the returned ID into the config cache via `services/site-schedule.service.ts::SiteScheduleService.addShiftToConfig`.
12. Contractor add/update/delete flows delegate to `api.service.ts::ApiService` and then apply the mutation locally through `services/site-context.service.ts::SiteContextService.addContractor`, `updateContractorLocal`, or `removeContractor`.
13. Invite CRUD and pending-member approval/rejection are handled by `services/invite.service.ts::InviteService`; revoked invites remain in state with status `revoked` (soft delete).
14. Smart group evaluation is client-side: `services/smart-group.service.ts::SmartGroupService.activateGroup` or `activateAdHocFilter` runs `services/selection-filter.service.ts::SelectionFilterService.evaluateQuery` and publishes `_matchedIds` and `_statistics`.
15. Layer rules are loaded on demand when the Layer Rules tab opens: `services/layer-rules.service.ts::LayerRulesService.loadLayerRules` fetches rules and defaults together via `forkJoin`.
16. Label styles are loaded per site by `services/label-style.service.ts::LabelStyleService.loadForSite`; on failure the cache falls back to `services/label-style.service.ts::LABEL_STYLE_DEFAULTS`.
17. Each `*-sync-binding.service.ts` registers a domain handler with `services/config-sync.service.ts::ConfigSyncService` in its constructor so catch-up replay after reconnection is handled; `services/config-sync.service.ts::ConfigSyncService.dispatch` wraps handler invocation in `try/catch` to isolate domain errors.
18. `services/contractor-visibility.service.ts::ContractorVisibilityService` tracks hidden contractors in `_hiddenContractorIds` and resets the set to empty on every site change.

## Side effects
- HTTP writes to backend: shift create/delete, contractor create/update/delete, invite create/revoke/resend, invite-link create/revoke, pending-member approve/reject, site visibility/elevation/planning update, site nuke.
- WebSocket `config_changed` broadcasts processed by sync bindings to update local caches without full reload.
- `localStorage` key `simoops_last_site_id` updated on site selection.
- BehaviorSubject mutations in `SiteContextService`, `SiteScheduleService`, `InviteService`, `SmartGroupService`, `LayerRulesService`, `LabelStyleService`, and `ContractorVisibilityService`.

## Failure modes
- `SiteContextService.selectedShift$` and `selectedDate$` are getters returning new `Observable` references each call; templates or downstream operators must cache the reference or use `context$` to avoid repeated subscriptions.
- `SiteContextService.selectSite` empties `_shifts`, `_contractors`, and `_siteMaps` until the respective loads complete; consumers reading synchronously see empty arrays.
- `SiteScheduleService.prepareSaveSiteConfig` returns only new shifts. The caller must create each via API and call `addShiftToConfig` with the returned ID; skipping this leaves the timeline cache incomplete.
- `LayerDefaultsService.loadForSite` is a no-op if defaults are already cached for the same site; force a refresh by calling `clear()` first.
- `InviteService.wsApplyInviteDeleted` flips status to `revoked` rather than removing the row; UI that expects removal must filter on status.
- `SmartGroupService.wsApplySmartGroupUpdated` treats an update for an unknown row as a create to handle sharing transitions; strict consumers must tolerate duplicates.
- `SiteSettingsHostComponent` uses `OnPush` and calls `cdr.markForCheck()` on invite changes because the template reads synchronous getters instead of async pipes.
- Sync bindings must be injected eagerly before the first WS broadcast; lazy injection misses early events and leaves caches stale.
- `ConfigSyncService.dispatch` catches handler errors to prevent one broken domain from killing others, but the failing domain’s local cache may drift until the next broadcast or a page reload.
