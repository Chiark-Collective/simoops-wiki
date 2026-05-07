---
service: backend
summary: "Email invites and shareable invite links"
paths: [backend/app/services/auth/invite_service.py, backend/app/services/auth/invite_link_service.py, backend/app/services/auth/keycloak_admin.py]
flows: [invite_accept_flow]
touches: [infra/data-stores]
external: [keycloak]
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose
Manage user invitation lifecycle via email-based invites and shareable invite
links, with Keycloak user provisioning and site membership creation.

## Interface
- `services/auth/invite_service.py::InviteService`
- `services/auth/invite_service.py::InviteService.create_invite` → UserInviteRead
- `services/auth/invite_service.py::InviteService.list_invites` → list[UserInviteRead]
- `services/auth/invite_service.py::InviteService.revoke_invite` → UUID (site_id)
- `services/auth/invite_service.py::InviteService.resend_invite` → None
- `services/auth/invite_service.py::InviteService.accept_pending_invites` → int (count)
- `services/auth/invite_link_service.py::InviteLinkService`
- `services/auth/invite_link_service.py::InviteLinkService.create_link` → InviteLinkRead
- `services/auth/invite_link_service.py::InviteLinkService.validate_link` → InviteLinkValidation
- `services/auth/invite_link_service.py::InviteLinkService.accept_link` → InviteLinkAcceptResponse
- `services/auth/invite_link_service.py::InviteLinkService.register_and_accept` → InviteLinkAcceptResponse
- `services/auth/invite_link_service.py::InviteLinkService.list_links` → list[InviteLinkRead]
- `services/auth/invite_link_service.py::InviteLinkService.revoke_link` → UUID (site_id)
- `services/auth/keycloak_admin.py::KeycloakAdminService`
- `services/auth/keycloak_admin.py::KeycloakAdminService.create_or_get_user` → str (kc user id)
- `services/auth/keycloak_admin.py::KeycloakAdminService.send_password_setup_email` → None
- `services/auth/keycloak_admin.py::KeycloakAdminService.create_user_with_password` → str (kc user id)
- `services/auth/keycloak_admin.py::KeycloakAdminService.get_user_by_email` → dict | None
- `services/auth/keycloak_admin.py::KeycloakAdminService.verify_user_password` → bool
- `services/auth/keycloak_admin.py::KeycloakAdminService.set_user_password` → None

## State
Omitted — all services are stateless; runtime state is in SQLModel session and
Keycloak Admin API.

## Internals
- `create_invite` calls `core/rbac.py::require_site_permission` with `Permission.invite_manage`
- Role hierarchy enforced by `core/permissions.py::can_assign_role`; superadmins bypass
- Duplicate pending invite for same email+site raises HTTP 409
- Keycloak user provisioning failure in `create_invite` is non-fatal; invite is
  created without `keycloak_user_id` and retried on `resend_invite`
- `create_or_get_user` sets `requiredActions: ["UPDATE_PASSWORD"]` so Keycloak
  sends a password-setup email via `send_password_setup_email`
- `create_user_with_password` bypasses the email flow by setting credentials
  directly; used by `register_and_accept`
- `accept_pending_invites` is called from `core/auth.py::_resolve_keycloak_user`
  on every login; idempotent via existing `SiteMembership` check
- `validate_link` is public and unauthenticated; returns structured validation
  result including site name, role, and contractor selection requirement
- `accept_link` is idempotent: existing membership returns current status and
  still increments `use_count`
- `register_and_accept` creates Keycloak user, SimOops `User`, and
  `SiteMembership` in one transaction
- `use_count` incremented via `sa_update` atomic expression to avoid lost writes
  under concurrent acceptance
- Viewer, client, and member invite links are auto-verified; coordinator and admin roles require coordinator approval
- Client links are cross-contractor by design — `contractor_id` is always None
- `accept_link` calls `ws_manager.invalidate_user_context` after commit when a membership changes from unverified → verified, or when a new auto-verified membership is created
- `accept_pending_invites` collects `invalidate_site_ids` for newly created memberships and calls `ws_manager.invalidate_user_context` after commit
- `broadcast_config_event` emitted on new membership creation in `accept_link`
- WS `context_invalidated` broadcast sent after membership creation in `accept_link` and `accept_pending_invites` to refresh cached auth state

## Touches
| resource | how | why |
|---|---|---|
| infra/data-stores | SQLModel select/insert on `UserInvite`, `InviteLink`, `SiteMembership`, `User` | Persist invites, links, memberships, and user records |
| external/keycloak | Admin API: create user, send email, set password | Identity provisioning and authentication |

## Gotchas
- Keycloak provisioning failure during `create_invite` does not block invite
  creation; the user may be invited without a Keycloak account
- `resend_invite` will attempt to provision the Keycloak user if missing; if it
  fails again, the call returns 502
- `register_and_accept` does not emit a config broadcast event (unlike
  `accept_link`); the new user has no active WebSocket session yet
- `verify_user_password` uses the Resource Owner Password Credentials grant;
  requires `directAccessGrantsEnabled=true` on the backend client
- python-keycloak uses synchronous `requests` under the hood; all wrapping
  methods dispatch via `asyncio.to_thread`
- Role hierarchy violation returns 403 with a detailed message including both
  the inviter and target role names
