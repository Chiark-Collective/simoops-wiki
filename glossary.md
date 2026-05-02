---
---

# Glossary

| Term | Definition |
|---|---|
| Bearer token | JWT presented in the `Authorization: Bearer <token>` header |
| JWKS | JSON Web Key Set; Keycloak publishes RS256 public keys via a JWKS endpoint |
| keycloak_sub | Keycloak subject identifier stored on `User.keycloak_sub`; primary user lookup key |
| Entity | A managed object in the planning cycle: token, zone, fence, section. Has geometry and state. |
| Token | A point-geometry entity representing a person or asset on site. |
| Zone | A polygon-geometry entity defining an area with safety rules. |
| Fence | A safety boundary; crossing triggers a clash. |
| Section | A subdivided area of a site for phased planning. |
| Shift | A temporal work unit; tokens are active within a shift. |
| Clash | A spatial or temporal violation between entities and safety rules. |
| Planning Cycle | The lifecycle of a site's plan: draft → active → archived. |
| OT | Operational Transformation; concurrency control for collaborative geometry edits. |
| Presence | Real-time user location and viewport sharing. |
| Room | A named broadcast channel, conventionally `site:{site_id}`. |
| SubscriptionContext | Pre-fetched permission data (`role`, `contractor_id`, `can_view_others`) passed to `subscribe()`. |
| Ephemeral broadcast | A non-persisted, non-sequenced, non-relayed WebSocket message (e.g., drag positions). |
| Entity event | A sequenced lifecycle broadcast (`entity_created`, `entity_updated`, `entity_deleted`). |
| Audience directive | Per-event privacy metadata (`owner_or_shared`, `non_owner`) restricting delivery. |
| Context invalidation | Broadcast of `context_invalidated` to force clients to re-subscribe and refresh cached permissions. |
| Self-echo prevention | Origin ID stamped on Redis-published messages so the sender does not re-process them. |
| Companion TTL key | Separate Redis key emulating per-field TTL on a Redis Hash. |
| Data lock | Site-level immutability boundary; entities with `end_at <= site.data_locked_before` cannot be modified by non-admins. |
| Site-scoped RBAC | Permission model where access is granted per-site via `SiteMembership`. |
| Superadmin bypass | System-level users (`is_superadmin=True`) skip all role-based and site-scoped checks. |
| Verified membership | A `SiteMembership` with `verified=True`; unverified memberships are invisible to RBAC. |
| Synthetic membership | In-memory `SiteMembership` created for superadmins lacking an explicit site record. |
| Contractor filter | `UUID | None` value used to scope entity queries; `None` means no contractor restriction. |
| Site | The top-level organizational unit; contains entities, shifts, users. |
| Schedule group | A collection of entities sharing a temporal pattern; resolved into occurrences per shift. |
| Occurrence | A concrete time-bound instance of a schedule group within a specific shift. |
| Reconcile | The process of aligning planned entity schedules with actual shift boundaries. |
| Vertex op | A WebSocket message encoding an operational-transform edit to polygon vertices. |
| OT buffer | In-memory ring buffer holding pending vertex ops before persistence. |
| Clash cache | Generation-keyed Redis cache storing computed clash results per site/shift. |
| Generation-based caching | Cache invalidation strategy using monotonic generation counters rather than timestamps. |
| Native row | A planning cycle row created directly in the cycle (`source_row_id` IS NULL). |
| Shadow row | A planning cycle row imported from baseline (`source_row_id` points to baseline). |
| Actualize | The operation that forks planned rows into actual baseline rows. |
| Carry-forward | Copying approved planned rows from a closed cycle into the next cycle. |
| Template schema | YAML/JSON structure defining report sections and their data providers. |
| Scene decision | A user's choice of which report scene (clash, delivery, etc.) to include. |
| Provider registry | Ordered registry of context providers; registration order determines dependency resolution. |
| COG | Cloud Optimized GeoTIFF; tiled raster format for efficient map serving. |
| Floor plan | A georeferenced image or GeoTIFF representing a building level. |
| Feature | A geometadata object: point, line, or polygon with properties and versioning. |
| Presence | WebSocket state tracking who is online, what they are editing, and their map viewport. |
| Heartbeat | Periodic `presence_heartbeat` message refreshing presence TTL in Redis. |
| Invite link | A shareable tokenized URL granting site access without email. |
| Text label | Site-wide permanent text annotation on the map; no temporal model, no clash participation. |
| Audit snapshot | A serialized entity state captured at mutation time; used for reverts and timeline reconstruction. |
| Rule profile | A named collection of activated clash rules with custom parameters; can be cloned and templated. |
| Rule version | A point-in-time snapshot of a single clash rule; supports rollback and audit. |
| Scene score | An aggregated severity metric for a set of clashes within a planning scene. |
| Clash cache generation | Monotonic counter per site/shift; cache keys include generation to detect invalidation. |
| JWKS cache | In-memory cache of Keycloak public keys; stale on prolonged outage. |
| Presigned URL | Time-limited S3 URL for direct client upload/download without proxying through the backend. |
