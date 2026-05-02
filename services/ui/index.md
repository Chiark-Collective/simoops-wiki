---
service: ui
summary: SimOops Angular frontend — standalone app with zoneless change detection, MapLibre map, and real-time WebSocket sync.
---

# UI

Angular standalone application. Boots via `bootstrapApplication` with zoneless change detection. OIDC auth via `angular-auth-oidc-client` → Keycloak. All state is RxJS `BehaviorSubject`-based.

## API Channels

| Page | Channel | What |
|---|---|---|
| [api/http.md](api/http.md) | HTTP | Domain-specific API wrappers (area, worker, plant, site, auth, clash, geometry, planning, report, revision, weather, export, geometadata, entity-support) |
| [api/websocket.md](api/websocket.md) | WebSocket | Real-time entity sync, presence, ephemeral positions, vertex ops |

## Modules

### App Shell & Auth

| Page | What |
|---|---|
| [modules/app-shell.md](modules/app-shell.md) | Bootstrap, routing, guards, HTTP interceptors |
| [modules/auth.md](modules/auth.md) | OIDC auth, UserService, login/join/site-selection pages |

### Dashboard & Shared

| Page | What |
|---|---|
| [modules/dashboard.md](modules/dashboard.md) | Composition root: layout, toolbar, dock-bar, panels, modal host, wiring |
| [modules/shared-ui.md](modules/shared-ui.md) | Reusable components, pipes, utils, constants |

### Map

| Page | What |
|---|---|
| [modules/map-core.md](modules/map-core.md) | MapLibre host, event wiring, source manager, subscription orchestrator |
| [modules/map-layers.md](modules/map-layers.md) | Declarative layer definitions, source utilities, visibility, raster sources |
| [modules/map-interaction.md](modules/map-interaction.md) | Drag handlers, vertex editing, context menus, selection tools |
| [modules/map-visuals.md](modules/map-visuals.md) | Grid, measurement, pulse animations, beacons, tooltips, scene overlays |
| [modules/map-floor-plans.md](modules/map-floor-plans.md) | Floor plan rendering, positioning, building focus coordinator |

### Entity Lifecycle

| Page | What |
|---|---|
| [modules/entity-store.md](modules/entity-store.md) | EntityStore, EntityService, API façade, domain API wrappers |
| [modules/entity-creation.md](modules/entity-creation.md) | Creation orchestrator, per-type handlers, creation host |
| [modules/entity-edit.md](modules/entity-edit.md) | Edit orchestrator, session, form initializers, save handlers, modal dispatch |
| [modules/entity-delete.md](modules/entity-delete.md) | Delete orchestrator, bulk operations |
| [modules/selection.md](modules/selection.md) | Selection, filtering, hover, visibility, centering, hidden entities |

### Planning & Clash

| Page | What |
|---|---|
| [modules/temporal-planning.md](modules/temporal-planning.md) | Temporal context, planning cycle, revision mode, gantt, schedule |
| [modules/clash-ui.md](modules/clash-ui.md) | Clash state, interaction, rules, profiles, resolution sync |

### Administration & Reports

| Page | What |
|---|---|
| [modules/site-admin.md](modules/site-admin.md) | Site context, configuration, contractors, shifts, invites, smart groups |
| [modules/reports.md](modules/reports.md) | Report orchestrator, session, wizard, scene capture, export |

### Real-time

| Page | What |
|---|---|
| [modules/realtime-sync.md](modules/realtime-sync.md) | WebSocket connection, event router, presence, offline queue, undo |

## Flows

| Page | Trigger |
|---|---|
| (pending) | Login → Site Select → Dashboard bootstrap |
| (pending) | Create entity on map |
| (pending) | Submit planning cycle |
| (pending) | Report generation and export |
| (pending) | WebSocket reconnection with catch-up |
