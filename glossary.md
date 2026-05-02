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
