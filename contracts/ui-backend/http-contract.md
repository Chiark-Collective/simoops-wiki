---
producer: ui
consumers: [backend]
schema: src/app/api/*.ts → api/routes/*.py
breaking_changes: []
---

## Purpose
Maps every frontend API service method to its backend HTTP endpoint handler.

## Consumers

| service | uses | flow |
|---|---|---|
| backend | HTTP routes | ui → backend request/response |

## Auth

| method | endpoint | backend handler |
|---|---|---|
| `AuthApi.getCurrentUser()` | GET `/api/auth/me` | `auth.py::get_me` |
| `AuthApi.changePassword()` | POST `/api/auth/change-password` | `auth.py::change_password` |
| `AuthApi.getUsersBulk()` | GET `/api/users/bulk` | `users.py::get_users_bulk` |
| `AuthApi.createUserInvite()` | POST `/api/invites/sites/{siteId}` | `invites.py::create_invite` |
| `AuthApi.listUserInvites()` | GET `/api/invites/sites/{siteId}` | `invites.py::list_invites` |
| `AuthApi.revokeUserInvite()` | DELETE `/api/invites/{inviteId}` | `invites.py::revoke_invite` |
| `AuthApi.resendUserInvite()` | POST `/api/invites/{inviteId}/resend` | `invites.py::resend_invite` |
| `AuthApi.createInviteLink()` | POST `/api/invite-links/sites/{siteId}` | `invite_links.py::create_invite_link` |
| `AuthApi.listInviteLinks()` | GET `/api/invite-links/sites/{siteId}` | `invite_links.py::list_invite_links` |
| `AuthApi.revokeInviteLink()` | DELETE `/api/invite-links/{linkId}` | `invite_links.py::revoke_invite_link` |
| `AuthApi.validateInviteLink()` | GET `/api/invite-links/validate/{token}` | `invite_links.py::validate_invite_link` |
| `AuthApi.acceptInviteLink()` | POST `/api/invite-links/accept/{token}` | `invite_links.py::accept_invite_link` |
| `AuthApi.registerViaInviteLink()` | POST `/api/invite-links/register/{token}` | `invite_links.py::register_via_invite_link` |
| `AuthApi.postAuthDiagEvent()` | POST `/api/diag/auth-event` | `diag.py::post_auth_event` |
| `AuthApi.listPendingMembers()` | GET `/api/memberships/sites/{siteId}/pending` | `memberships.py::list_pending_members` |
| `AuthApi.approveMember()` | POST `/api/memberships/{membershipId}/approve` | `memberships.py::approve_member` |
| `AuthApi.rejectMember()` | DELETE `/api/memberships/{membershipId}` | `memberships.py::reject_member` |

## Site

| method | endpoint | backend handler |
|---|---|---|
| `SiteApi.listSites()` | GET `/api/sites/` | `sites.py::list_sites` |
| `SiteApi.listSitesPublic()` | GET `/api/sites/public` | `sites.py::list_sites_public` |
| `SiteApi.updateSite()` | PATCH `/api/sites/{siteId}` | `sites.py::update_site` — `site_settings` (admin) for planning toggles, `site_settings_basic` (coordinator+) for other fields |
| `SiteApi.setDataLock()` | POST `/api/sites/{siteId}/lock` | `sites.py::set_data_lock` |
| `SiteApi.nukeSiteData()` | DELETE `/api/sites/{siteId}/nuke` | `sites.py::nuke_site_data` |
| `SiteApi.listShifts()` | GET `/api/shifts/` | `shifts.py::list_shifts` |
| `SiteApi.createShift()` | POST `/api/shifts/` | `shifts.py::create_shift` |
| `SiteApi.deleteShift()` | DELETE `/api/shifts/{shiftId}` | `shifts.py::delete_shift` |
| `SiteApi.listContractors()` | GET `/api/contractors/` | `contractors.py::list_contractors` |
| `SiteApi.createContractor()` | POST `/api/contractors/` | `contractors.py::create_contractor` |
| `SiteApi.updateContractor()` | PATCH `/api/contractors/{contractorId}` | `contractors.py::update_contractor` |
| `SiteApi.deleteContractor()` | DELETE `/api/contractors/{contractorId}` | `contractors.py::delete_contractor` |
| `SiteApi.uploadContractorLogo()` | PUT `/api/contractors/{contractorId}/logo` | `contractors.py::upload_logo` |
| `SiteApi.deleteContractorLogo()` | DELETE `/api/contractors/{contractorId}/logo` | `contractors.py::delete_logo` |
| `SiteApi.getContractorLogoImage()` | GET `/api/contractors/{contractorId}/logo/image` | `contractors.py::get_logo_image` — public, no auth, Cache-Control 5min |
| `SiteApi.listContractorsPublic()` | GET `/api/contractors/public` | `contractors.py::list_contractors_public` |
| `SiteApi.uploadSiteMap()` | POST `/api/site-maps/upload` | `site_maps.py::upload_site_map` |
| `SiteApi.uploadSiteMapWithProgress()` | POST `/api/site-maps/upload?site_id={siteId}` | `site_maps.py::upload_site_map` *(multipart/progress)* |
| `SiteApi.calibrateSiteMap()` | POST `/api/site-maps/{siteMapId}/calibrate` | `site_maps.py::calibrate_site_map` |
| `SiteApi.getLatestSiteMap()` | GET `/api/site-maps/sites/{siteId}/latest-map` | `site_maps.py::get_latest_site_map` |
| `SiteApi.getSiteMap()` | GET `/api/site-maps/{siteMapId}` | `site_maps.py::get_site_map` |
| `SiteApi.listSiteMaps()` | GET `/api/site-maps/sites/{siteId}/maps` | `site_maps.py::list_site_maps` |
| `SiteApi.getLabelStyles()` | GET `/api/sites/{siteId}/label-styles/` | `label_styles.py::get_label_styles` |
| `SiteApi.updateLabelStyles()` | PUT `/api/sites/{siteId}/label-styles/` | `label_styles.py::upsert_label_styles` |

## Weather

| method | endpoint | backend handler |
|---|---|---|
| `WeatherApi.getTimeline()` | GET `/api/weather/sites/{siteId}/timeline` | `weather.py::get_timeline` |

## Geometry

| method | endpoint | backend handler |
|---|---|---|
| `GeometryApi.getPendingCuts()` | GET `/api/geometry/pending-cuts/{featureId}` | `geometry_operations.py::get_pending_cuts` |
| `GeometryApi.cutHole()` | POST `/api/geometry/cut-hole` | `geometry_operations.py::cut_hole` |
| `GeometryApi.undoCut()` | POST `/api/geometry/undo-cut/{historyId}` | `geometry_operations.py::undo_cut` |
| `GeometryApi.checkOverlaps()` | POST `/api/geometry/check-overlaps` | `geometry_operations.py::check_overlaps` |
| `GeometryApi.getGeometryHistory()` | GET `/api/geometry/history/{featureId}` | `geometry_operations.py::get_feature_history` |
| `GeometryApi.getLayerTypeRules()` | GET `/api/geometry/rules` | `geometry_operations.py::list_layer_type_rules` |
| `GeometryApi.getLayerTypeDefaults()` | GET `/api/geometry/defaults` | `geometry_operations.py::list_layer_type_defaults` |

## Geometadata

| method | endpoint | backend handler |
|---|---|---|
| `GeometadataApi.validateBundle()` | POST `/api/bundle-import/validate` | `bundle_import.py::validate_bundle_route` |
| `GeometadataApi.executeBundle()` | POST `/api/bundle-import/execute` | `bundle_import.py::execute_bundle_route` |
| `GeometadataApi.uploadGeometadataLayer()` | POST `/api/geometadata/layers/upload` | `geometadata.py::upload_geometadata_layer` |
| `GeometadataApi.listGeometadataLayers()` | GET `/api/geometadata/layers` | `geometadata.py::list_layers` |
| `GeometadataApi.createGeometadataLayer()` | POST `/api/geometadata/layers` | `geometadata.py::create_layer` |
| `GeometadataApi.getGeometadataLayer()` | GET `/api/geometadata/layers/{layerId}` | `geometadata.py::get_layer` |
| `GeometadataApi.updateGeometadataLayer()` | PATCH `/api/geometadata/layers/{layerId}` | `geometadata.py::update_layer` |
| `GeometadataApi.deleteGeometadataLayer()` | DELETE `/api/geometadata/layers/{layerId}` | `geometadata.py::delete_layer` |
| `GeometadataApi.listGeometadataFeatures()` | GET `/api/geometadata/layers/{layerId}/features` | `geometadata.py::list_features` |
| `GeometadataApi.createGeometadataFeature()` | POST `/api/geometadata/zones` | `geometadata.py::create_zone_feature` |
| `GeometadataApi.getGeometadataFeature()` | GET `/api/geometadata/features/{featureId}` | `geometadata.py::get_feature` |
| `GeometadataApi.updateGeometadataFeature()` | PATCH `/api/geometadata/features/{featureId}` | `geometadata.py::update_feature` |
| `GeometadataApi.deleteGeometadataFeature()` | DELETE `/api/geometadata/features/{featureId}` | `geometadata.py::delete_feature` |
| `GeometadataApi.getBuildingAtPoint()` | GET `/api/geometadata/building-at-point` | `geometadata.py::query_building_at_point` |
| `GeometadataApi.listFeaturesAtTime()` | GET `/api/geometadata/features/at-time` | `geometadata.py::list_features_at_time` |
| `GeometadataApi.getFeatureVersionHistory()` | GET `/api/geometadata/features/{featureId}/history` | `geometadata.py::get_feature_history` |
| `GeometadataApi.getFeatureAtTime()` | GET `/api/geometadata/features/{featureId}/at-time` | `geometadata.py::get_feature_at_time` |
| `GeometadataApi.getFloorPlans()` | GET `/api/floor-plans/{featureId}` | `floor_plans.py::list_floor_plans` |
| `GeometadataApi.getFloorPlan()` | GET `/api/floor-plans/{featureId}/{levelIndex}` | `floor_plans.py::get_floor_plan` |
| `GeometadataApi.uploadFloorPlan()` | POST `/api/floor-plans/upload` | `floor_plans.py::upload_floor_plan` |
| `GeometadataApi.deleteFloorPlan()` | DELETE `/api/floor-plans/{floorPlanId}` | `floor_plans.py::delete_floor_plan` |
| `GeometadataApi.uploadFloorPlanImage()` | POST `/api/floor-plans/upload-image` | `floor_plans.py::upload_floor_plan_image` |
| `GeometadataApi.updateFloorPlanPlacement()` | PATCH `/api/floor-plans/{floorPlanId}/placement` | `floor_plans.py::update_floor_plan_placement` |
| `GeometadataApi.getFloorPlanImageUrl()` | GET `/api/floor-plans/{floorPlanId}/image-url` | `floor_plans.py::get_floor_plan_image_url` |
| `GeometadataApi.getFloorPlanImageBlob()` | GET `/api/floor-plans/{floorPlanId}/image` | `floor_plans.py::get_floor_plan_image` |

## Export / Permits

| method | endpoint | backend handler |
|---|---|---|
| `ExportApi.exportGeoJson()` | GET `/api/exports/geojson` | `exports.py::export_geojson` |
| `ExportApi.getPermitFormats()` | GET `/api/permits/formats` | `permits.py::list_formats` |
| `ExportApi.uploadPermits()` | POST `/api/permits/upload` | `permits.py::upload_permits` |
| `ExportApi.listPermits()` | GET `/api/permits` | `permits.py::list_permits` |
| `ExportApi.listPermitSets()` | GET `/api/permits/sets` | `permits.py::list_permit_sets` |
| `ExportApi.deletePermitSet()` | DELETE `/api/permits/sets/{setId}` | `permits.py::delete_permit_set` |
| `ExportApi.reResolveLocations()` | POST `/api/permits/re-resolve` | `permits.py::re_resolve_locations` |
| `ExportApi.recordPermitCreation()` | POST `/api/permits/{permitId}/record-creation` | `permits.py::record_permit_creation` |
| `ExportApi.createEntityFromPermit()` | POST `/api/permits/{permitId}/create-entity` | `permits.py::create_entity_from_permit` |

## Planning

| method | endpoint | backend handler |
|---|---|---|
| `PlanningApi.createCycle()` | POST `/api/planning-cycles/` | `planning.py::create_cycle` |
| `PlanningApi.listCycles()` | GET `/api/planning-cycles/` | `planning.py::list_cycles` |
| `PlanningApi.getCycle()` | GET `/api/planning-cycles/{cycleId}` | `planning.py::get_cycle` |
| `PlanningApi.updateStatus()` | PATCH `/api/planning-cycles/{cycleId}/status` | `planning.py::update_cycle_status` |
| `PlanningApi.listSubmissions()` | GET `/api/planning-cycles/{cycleId}/submissions` | `planning.py::list_submissions` |
| `PlanningApi.createSubmission()` | POST `/api/planning-cycles/{cycleId}/submissions` | `planning.py::create_submission` |
| `PlanningApi.submissionInsights()` | GET `/api/planning-cycles/{cycleId}/submission-insights` | `planning.py::list_submission_insights` |
| `PlanningApi.submissionInsightDetail()` | GET `/api/planning-cycles/{cycleId}/submission-insights/{contractorId}` | `planning.py::get_submission_insight_detail` |
| `PlanningApi.pendingSummaries()` | GET `/api/planning-cycles/{cycleId}/pending-summaries` | `planning.py::list_pending_summaries` |
| `PlanningApi.submitPlan()` | POST `/api/planning-cycles/{cycleId}/submit` | `planning.py::submit_plan` |
| `PlanningApi.submitAllPending()` | POST `/api/planning-cycles/{cycleId}/submit-all-pending` | `planning.py::submit_all_pending` |
| `PlanningApi.approveSubmission()` | POST `/api/planning-cycles/{cycleId}/approve-submission` | `planning.py::approve_submission` |
| `PlanningApi.approveAllSubmitted()` | POST `/api/planning-cycles/{cycleId}/approve-all-submitted` | `planning.py::approve_all_submitted` |
| `PlanningApi.requestRevision()` | POST `/api/planning-cycles/{cycleId}/request-revision` | `planning.py::request_revision` |
| `PlanningApi.submissionSummary()` | GET `/api/planning-cycles/{cycleId}/submission-summary` | `planning.py::submission_summary` |
| `PlanningApi.actualize()` | POST `/api/planning-cycles/{cycleId}/actualize` | `planning.py::actualize_cycle` |
| `PlanningApi.compare()` | GET `/api/planning-cycles/{cycleId}/compare` | `planning.py::compare_cycle` |
| `PlanningApi.carryForward()` | POST `/api/planning-cycles/{sourceCycleId}/carry-forward` | `planning.py::carry_forward` |
| `PlanningApi.clashDiff()` | GET `/api/planning-cycles/{cycleId}/clash-diff` | `planning.py::clash_diff` |
| `PlanningApi.importBaseline()` | POST `/api/planning-cycles/{cycleId}/import-baseline` | `planning.py::import_baseline` |

## Plant

| method | endpoint | backend handler |
|---|---|---|
| `PlantApi.listPlant()` | GET `/api/plant` | `plant.py::list_plant` |
| `PlantApi.createPlant()` | POST `/api/plant` | `plant.py::create_plant` |
| `PlantApi.updatePlant()` | PATCH `/api/plant/{plantId}` | `plant.py::update_plant` |
| `PlantApi.deletePlant()` | DELETE `/api/plant/{plantId}` | `plant.py::delete_plant` |
| `PlantApi.restorePlant()` | POST `/api/plant/{plantId}/restore` | `plant.py::restore_plant` |
| `PlantApi.deletePlantPositionGroup()` | DELETE `/api/plant/position-group/{sourcePlantId}` | `plant.py::delete_plant_position_group` |
| `PlantApi.copyPlantsFromDatetimeRange()` | POST `/api/plant/copy-from-range` | `plant.py::copy_plant_from_range` |
| `PlantApi.createPlantSchedule()` | POST `/api/plant/create-schedule` | `plant.py::create_plant_schedule` |
| `PlantApi.getPlantScheduleGroup()` | GET `/api/plant/schedule-group/{groupId}` | `plant.py::get_plant_schedule_group` |
| `PlantApi.updatePlantScheduleGroup()` | PATCH `/api/plant/schedule-group/{groupId}` | `plant.py::update_plant_schedule_group` |
| `PlantApi.deletePlantScheduleGroup()` | DELETE `/api/plant/schedule-group/{groupId}` | `plant.py::delete_plant_schedule_group` |
| `PlantApi.reconcilePlantScheduleGroup()` | PUT `/api/plant/schedule-group/{groupId}/reconcile` | `plant.py::reconcile_plant_schedule_group` |
| `PlantApi.convertPlantToSchedule()` | POST `/api/plant/{plantId}/convert-to-schedule` | `plant.py::convert_plant_to_schedule` |

## Worker (Token)

| method | endpoint | backend handler |
|---|---|---|
| `WorkerApi.listTokens()` | GET `/api/workers/` | `workers.py::list_workers` |
| `WorkerApi.createToken()` | POST `/api/workers/` | `workers.py::create_worker` |
| `WorkerApi.updateToken()` | PATCH `/api/workers/{tokenId}` | `workers.py::update_worker` |
| `WorkerApi.patchToken()` | PATCH `/api/workers/{tokenId}` | `workers.py::update_worker` |
| `WorkerApi.deleteToken()` | DELETE `/api/workers/{tokenId}` | `workers.py::delete_worker` |
| `WorkerApi.restoreToken()` | POST `/api/workers/{tokenId}/restore` | `workers.py::restore_worker` |
| `WorkerApi.copyTokensFromDatetimeRange()` | POST `/api/workers/copy-from-range` | `workers.py::copy_workers_from_range` |
| `WorkerApi.batchDeleteTokens()` | DELETE `/api/workers/batch` | `workers.py::batch_delete_workers` |
| `WorkerApi.createTokenSchedule()` | POST `/api/workers/create-schedule` | `workers.py::create_worker_schedule` |
| `WorkerApi.getTokenScheduleGroup()` | GET `/api/workers/schedule-group/{groupId}` | `workers.py::get_worker_schedule_group` |
| `WorkerApi.updateTokenScheduleGroup()` | PATCH `/api/workers/schedule-group/{groupId}` | `workers.py::update_worker_schedule_group` |
| `WorkerApi.deleteTokenScheduleGroup()` | DELETE `/api/workers/schedule-group/{groupId}` | `workers.py::delete_worker_schedule_group` |
| `WorkerApi.reconcileTokenScheduleGroup()` | PUT `/api/workers/schedule-group/{groupId}/reconcile` | `workers.py::reconcile_worker_schedule_group` |
| `WorkerApi.convertTokenToSchedule()` | POST `/api/workers/{tokenId}/convert-to-schedule` | `workers.py::convert_worker_to_schedule` |

## Report

| method | endpoint | backend handler |
|---|---|---|
| `ReportApi.listTemplates()` | GET `/api/reports/templates` | `reports.py::list_templates` |
| `ReportApi.getTemplate()` | GET `/api/reports/templates/{templateId}` | `reports.py::get_template` |
| `ReportApi.createTemplate()` | POST `/api/reports/templates` | `reports.py::create_template` |
| `ReportApi.deleteTemplate()` | DELETE `/api/reports/templates/{templateId}` | `reports.py::delete_template` |
| `ReportApi.createSession()` | POST `/api/reports/sessions` | `reports.py::create_session` |
| `ReportApi.listSessions()` | GET `/api/reports/sessions` | `reports.py::list_sessions` |
| `ReportApi.getSession()` | GET `/api/reports/sessions/{sessionId}` | `reports.py::get_session` |
| `ReportApi.updateSession()` | PATCH `/api/reports/sessions/{sessionId}` | `reports.py::update_session` |
| `ReportApi.completeSession()` | POST `/api/reports/sessions/{sessionId}/complete` | `reports.py::complete_session` |
| `ReportApi.deleteSession()` | DELETE `/api/reports/sessions/{sessionId}` | `reports.py::delete_session` |
| `ReportApi.refreshContext()` | POST `/api/reports/sessions/{sessionId}/refresh-context` | `reports.py::refresh_context` |
| `ReportApi.exportPdf()` | POST `/api/reports/sessions/{sessionId}/export/pdf` | `reports.py::export_pdf` |
| `ReportApi.exportDocx()` | POST `/api/reports/sessions/{sessionId}/export/docx` | `reports.py::export_docx` |

## Revision / Audit

| method | endpoint | backend handler |
|---|---|---|
| `RevisionApi.getSummary()` | GET `/api/sites/{siteId}/snapshot-revision` | `sites.py::get_snapshot_revision_summary` |
| `RevisionApi.listWorkersAtTime()` | GET `/api/workers/at-time` | `workers.py::list_workers_at_time` |
| `RevisionApi.listPlantAtTime()` | GET `/api/plant/at-time` | `plant.py::list_plant_at_time` |
| `RevisionApi.listFeaturesAtTime()` | GET `/api/geometadata/features/at-time` | `geometadata.py::list_features_at_time` |
| `RevisionApi.listDeliveriesAtTime()` | GET `/api/deliveries/at-time` | `deliveries.py::list_deliveries_at_time` |
| `RevisionApi.listPoisAtTime()` | GET `/api/pois/at-time` | `poi.py::list_pois_at_time` |
| `RevisionApi.listTextLabelsAtTime()` | GET `/api/text-labels/at-time` | `text_labels.py::list_text_labels_at_time` |
| `RevisionApi.listClashesAtTime()` | GET `/api/clashes/at-time` | `clashes.py::list_clashes_at_time` |
| `RevisionApi.listFloorPlansAtTime()` | GET `/api/floor-plans/at-time` | `floor_plans.py::list_floor_plans_at_time` |
| `RevisionApi.listTimeline()` | GET `/api/audit/site/{siteId}/timeline` | `audit.py::get_site_revision_timeline` |
| `RevisionApi.loadRevision()` | *(fan-out composite — calls multiple `/at-time` endpoints)* | — |
| `AuditApi.getEntityHistory()` | GET `/api/audit/entity/{entityType}/{entityId}` | `audit.py::get_entity_history` |
| `AuditApi.revertToEntry()` | POST `/api/audit/revert/{entryId}` | `audit.py::revert_to_entry` |
| `AuditApi.getSiteAuditLog()` | GET `/api/audit/site/{siteId}` | `audit.py::get_site_audit_log` |

## Area

| method | endpoint | backend handler |
|---|---|---|
| `AreaApi.listAreas()` | GET `/api/geometadata/areas` | `geometadata.py::list_areas` |
| `AreaApi.createArea()` | POST `/api/geometadata/zones` | `geometadata.py::create_zone_feature` |
| `AreaApi.updateArea()` | PATCH `/api/geometadata/features/{areaId}` | `geometadata.py::update_feature` |
| `AreaApi.deleteArea()` | DELETE `/api/geometadata/features/{areaId}` | `geometadata.py::delete_feature` |
| `AreaApi.restoreArea()` | POST `/api/geometadata/features/{areaId}/restore` | `geometadata.py::restore_feature` |
| `AreaApi.copyAreasFromDatetimeRange()` | POST `/api/geometadata/areas/copy-from-range` | `geometadata.py::copy_areas_from_range` |
| `AreaApi.createAreaSchedule()` | POST `/api/geometadata/areas/create-schedule` | `geometadata.py::create_area_schedule` |
| `AreaApi.getAreaScheduleGroup()` | GET `/api/geometadata/areas/schedule-group/{groupId}` | `geometadata.py::get_area_schedule_group` |
| `AreaApi.updateAreaScheduleGroup()` | PATCH `/api/geometadata/areas/schedule-group/{groupId}` | `geometadata.py::update_area_schedule_group` |
| `AreaApi.deleteAreaScheduleGroup()` | DELETE `/api/geometadata/areas/schedule-group/{groupId}` | `geometadata.py::delete_area_schedule_group` |
| `AreaApi.reconcileAreaScheduleGroup()` | PUT `/api/geometadata/areas/schedule-group/{groupId}/reconcile` | `geometadata.py::reconcile_area_schedule_group` |
| `AreaApi.convertAreaToSchedule()` | POST `/api/geometadata/areas/{areaId}/convert-to-schedule` | `geometadata.py::convert_area_to_schedule` |

## Entity Support

### Roads

| method | endpoint | backend handler |
|---|---|---|
| `EntitySupportApi.listRoads()` | GET `/api/geometadata/features` | `geometadata.py::list_features_by_type` |
| `EntitySupportApi.createRoad()` | POST `/api/geometadata/zones` | `geometadata.py::create_zone_feature` |
| `EntitySupportApi.updateRoad()` | PATCH `/api/geometadata/features/{roadId}` | `geometadata.py::update_feature` |
| `EntitySupportApi.deleteRoad()` | DELETE `/api/geometadata/features/{roadId}` | `geometadata.py::delete_feature` |

### Deliveries

| method | endpoint | backend handler |
|---|---|---|
| `EntitySupportApi.listDeliveries()` | GET `/api/deliveries/` | `deliveries.py::list_deliveries` |
| `EntitySupportApi.createDelivery()` | POST `/api/deliveries/` | `deliveries.py::create_delivery` |
| `EntitySupportApi.updateDelivery()` | PATCH `/api/deliveries/{deliveryId}` | `deliveries.py::update_delivery` |
| `EntitySupportApi.deleteDelivery()` | DELETE `/api/deliveries/{deliveryId}` | `deliveries.py::delete_delivery` |
| `EntitySupportApi.restoreDelivery()` | POST `/api/deliveries/{deliveryId}/restore` | `deliveries.py::restore_delivery` |

### Points of Interest

| method | endpoint | backend handler |
|---|---|---|
| `EntitySupportApi.listPoIs()` | GET `/api/pois/` | `poi.py::list_pois` |
| `EntitySupportApi.createPoI()` | POST `/api/pois/` | `poi.py::create_poi` |
| `EntitySupportApi.updatePoI()` | PATCH `/api/pois/{poiId}` | `poi.py::update_poi` |
| `EntitySupportApi.deletePoI()` | DELETE `/api/pois/{poiId}` | `poi.py::delete_poi` |

### Text Labels

| method | endpoint | backend handler |
|---|---|---|
| `EntitySupportApi.listTextLabels()` | GET `/api/text-labels/` | `text_labels.py::list_text_labels` |
| `EntitySupportApi.createTextLabel()` | POST `/api/text-labels/` | `text_labels.py::create_text_label` |
| `EntitySupportApi.updateTextLabel()` | PATCH `/api/text-labels/{labelId}` | `text_labels.py::update_text_label` |
| `EntitySupportApi.deleteTextLabel()` | DELETE `/api/text-labels/{labelId}` | `text_labels.py::delete_text_label` |

### Smart Groups

| method | endpoint | backend handler |
|---|---|---|
| `EntitySupportApi.listSmartGroups()` | GET `/api/smart-groups/` | `smart_groups.py::list_smart_groups` |
| `EntitySupportApi.createSmartGroup()` | POST `/api/smart-groups/` | `smart_groups.py::create_smart_group` |
| `EntitySupportApi.getSmartGroup()` | GET `/api/smart-groups/{groupId}` | `smart_groups.py::get_smart_group` |
| `EntitySupportApi.updateSmartGroup()` | PATCH `/api/smart-groups/{groupId}` | `smart_groups.py::update_smart_group` |
| `EntitySupportApi.deleteSmartGroup()` | DELETE `/api/smart-groups/{groupId}` | `smart_groups.py::delete_smart_group` |
| `EntitySupportApi.evaluateSmartGroup()` | GET `/api/smart-groups/{groupId}/evaluate` | `smart_groups.py::evaluate_smart_group` |
| `EntitySupportApi.evaluateAdHocQuery()` | POST `/api/smart-groups/evaluate` | `smart_groups.py::evaluate_adhoc_query` |

### Bulk Import

| method | endpoint | backend handler |
|---|---|---|
| `EntitySupportApi.validateBulkImport()` | POST `/api/import/validate` | `bulk_import.py::validate_import` |
| `EntitySupportApi.executeBulkImport()` | POST `/api/import/execute` | `bulk_import.py::execute_import` |
| `EntitySupportApi.downloadImportTemplate()` | GET `/api/import/template/{entityType}` | `bulk_import.py::download_template` |

### Alerts

| method | endpoint | backend handler |
|---|---|---|
| `EntitySupportApi.listAlerts()` | GET `/api/alerts/` | `alerts.py::list_alerts` |
| `EntitySupportApi.createAlert()` | POST `/api/alerts/` | `alerts.py::create_alert` |
| `EntitySupportApi.getAlert()` | GET `/api/alerts/{alertId}` | `alerts.py::get_alert` |
| `EntitySupportApi.updateAlert()` | PATCH `/api/alerts/{alertId}` | `alerts.py::update_alert` |
| `EntitySupportApi.deleteAlert()` | DELETE `/api/alerts/{alertId}` | `alerts.py::delete_alert` |
| `EntitySupportApi.resolveAlert()` | POST `/api/alerts/{alertId}/resolve` | `alerts.py::resolve_alert` |
| `EntitySupportApi.unresolveAlert()` | POST `/api/alerts/{alertId}/unresolve` | `alerts.py::unresolve_alert` |
| `EntitySupportApi.getAlertActivity()` | GET `/api/alerts/{alertId}/activity` | `alerts.py::get_activity` |

## Clash

### Detection

| method | endpoint | backend handler |
|---|---|---|
| `ClashApi.listClashes()` | GET `/api/clashes` | `clashes.py::list_clashes` — 15s timeout → 504 |
| `ClashApi.listClashesAtTime()` | GET `/api/clashes/at-time` | `clashes.py::list_clashes_at_time` — optional `?involving=<kind>/<uuid>` filter |
| `ClashApi.resolveClash()` | POST `/api/clashes/resolve` | `clashes.py::resolve_clash_endpoint` |
| `ClashApi.resolveClashBulk()` | POST `/api/clashes/resolve-bulk` | `clashes.py::resolve_bulk_clashes_endpoint` |
| `ClashApi.unresolveClash()` | POST `/api/clashes/unresolve` | `clashes.py::unresolve_clash_endpoint` |

### Rules

| method | endpoint | backend handler |
|---|---|---|
| `ClashApi.listClashRules()` | GET `/api/clash-rules` | `clash_rules.py::list_clash_rules` |
| `ClashApi.getClashRule()` | GET `/api/clash-rules/{ruleId}` | `clash_rules.py::get_clash_rule` |
| `ClashApi.createClashRule()` | POST `/api/clash-rules` | `clash_rules.py::create_clash_rule` |
| `ClashApi.updateClashRule()` | PATCH `/api/clash-rules/{ruleId}` | `clash_rules.py::update_clash_rule` |
| `ClashApi.deleteClashRule()` | DELETE `/api/clash-rules/{ruleId}` | `clash_rules.py::delete_clash_rule` |
| `ClashApi.getClashRuleHistory()` | GET `/api/clash-rules/{ruleId}/history` | `clash_rules.py::get_rule_history` |
| `ClashApi.getClashRuleVersion()` | GET `/api/clash-rules/{ruleId}/versions/{version}` | `clash_rules.py::get_rule_version` |
| `ClashApi.revertClashRule()` | POST `/api/clash-rules/{ruleId}/revert/{version}` | `clash_rules.py::revert_rule_to_version` |
| `ClashApi.diffClashRuleVersions()` | GET `/api/clash-rules/{ruleId}/diff` | `clash_rules.py::diff_rule_versions` |
| `ClashApi.getClashRuleDsl()` | GET `/api/clash-rules/{ruleId}/dsl` | `clash_rules.py::get_rule_dsl` |
| `ClashApi.previewClashRuleDsl()` | POST `/api/clash-rules/dsl/preview` | `clash_rules.py::preview_rule_dsl` |

### Rule Profiles

| method | endpoint | backend handler |
|---|---|---|
| `ClashApi.listRuleProfiles()` | GET `/api/rule-profiles` | `rule_profiles.py::list_rule_profiles` |
| `ClashApi.getRuleProfile()` | GET `/api/rule-profiles/{profileId}` | `rule_profiles.py::get_rule_profile` |
| `ClashApi.createRuleProfile()` | POST `/api/rule-profiles` | `rule_profiles.py::create_rule_profile` |
| `ClashApi.updateRuleProfile()` | PATCH `/api/rule-profiles/{profileId}` | `rule_profiles.py::update_rule_profile` |
| `ClashApi.deleteRuleProfile()` | DELETE `/api/rule-profiles/{profileId}` | `rule_profiles.py::delete_rule_profile` |
| `ClashApi.activateRuleProfile()` | POST `/api/rule-profiles/{profileId}/activate` | `rule_profiles.py::activate_profile` |
| `ClashApi.cloneRuleProfile()` | POST `/api/rule-profiles/{profileId}/clone` | `rule_profiles.py::clone_profile` |
| `ClashApi.listProfileRules()` | GET `/api/rule-profiles/{profileId}/rules` | `rule_profiles.py::list_profile_rules` |
