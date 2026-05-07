---
trigger: { channel: http, ref: "GET /api/invite-links/{token}/validate | POST /api/invite-links/{token}/accept | POST /api/invite-links/{token}/register" }
services: [backend]
contracts: []
external: [keycloak]
---

## Trigger
User clicks a shareable invite link or submits the accept/registration form.

## Steps
1. Frontend calls `validate_link` with the invite token
2. `services/auth/invite_link_service.py::InviteLinkService.validate_link`
   checks token existence, `active` status, and expiry
3. Authenticated user submits accept → `accept_link`;
   unauthenticated user submits registration → `register_and_accept`
4. For `register_and_accept`:
   `services/auth/keycloak_admin.py::KeycloakAdminService.create_user_with_password`
   creates a Keycloak user with pre-set credentials
5. `services/auth/invite_link_service.py::InviteLinkService._validate_contractor_for_link`
   resolves and validates `contractor_id` (None for client role)
6. `services/auth/invite_link_service.py::InviteLinkService._create_membership_for_link`
    creates a `SiteMembership`; viewer, client, and member roles are auto-verified; coordinator and admin remain pending approval
7. `use_count` incremented atomically via `sa_update` to prevent lost writes
8. For `accept_link` with new membership:
    `services/config_broadcast.py::broadcast_config_event` emits a
    `membership.created` event to the site room
9. `core/websocket_manager.py::WebSocketManager.invalidate_user_context`
    broadcasts `context_invalidated` to force permission refresh
10. For `accept_pending_invites` (login path):
    `services/auth/invite_service.py::InviteService.accept_pending_invites`
    collects newly created memberships and calls `invalidate_user_context`
    per site after commit

## Side effects
- Keycloak user INSERT (registration path only)
- `User` record INSERT (registration path only)
- `SiteMembership` INSERT
- `InviteLink.use_count` atomic increment
- Config broadcast event (`membership.created`) on new membership acceptance
- WebSocket `context_invalidated` broadcast on new membership creation in `accept_link`
- WebSocket `context_invalidated` broadcast on new membership creation in `accept_pending_invites` (login path)

## Failure modes
| Failure | Detection | Handling |
|---|---|---|
| Invalid/expired/revoked link | `validate_link` or `_require_active_link` | 400/404 with descriptive message |
| Stale WebSocket cache after link acceptance | `invalidate_user_context` broadcast failure | Best-effort try/except; stale until next subscribe |
| Member role auto-verify | `_should_auto_verify` now includes `member` | Coordinator and admin still require explicit approval |
| Email already exists in Keycloak | `create_user_with_password` raises `ValueError` | 409 Conflict |
| Keycloak unreachable | Generic exception in admin call | 502 Bad Gateway |
| Contractor required but missing | `_validate_contractor_for_link` | 400 with requirement detail |
| Invalid contractor for site | `contractor.site_id != link.site_id` | 400 with invalid detail |
| Role hierarchy violation | `can_assign_role` check on link creation | 403 Forbidden (creation time, not acceptance) |
