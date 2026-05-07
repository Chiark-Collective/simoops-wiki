---
last_verified_commit: c56ee3d5
---

# Build

Cross-cutting CI/CD configuration.

## Pipeline

GitHub Actions (`.github/workflows/`) — **no build/test/deploy pipeline exists.**

| Workflow | Trigger | Action |
|---|---|---|
| `lint.yml` | PR / push to main | `make frontend-lint` (unmarked `as any` / `as unknown as` cast check) |
| `claude.yml` | `@claude` in issue/PR comments | Claude Code AI response |
| `claude-code-review.yml` | PR open/sync | Claude Code AI review |

Backend pytest, frontend Karma, and Playwright E2E are **not in CI** — they need Docker infrastructure and secrets.

## Deployment

All deployment is manual via Makefile targets. No automated deploy pipeline.

### Development

```bash
make local-up      # Start Docker stack + Angular dev server + migrations + Keycloak roles
make local-down    # Stop frontend dev server + Docker stack
make local-reset   # Full reset: down, remove volumes, rebuild, migrate, seed, start
```

Docker Compose (`docker-compose.yml`) starts: db, backend (hot-reload), minio, minio-setup, titiler, redis, keycloak (dev mode), mailpit.
Frontend runs via `ng serve` on port 4202. Node `proxy.mjs` on port 3000 routes API/titiler/Keycloak traffic.

### Production (Netcup VPS)

1. Provision VPS, install Docker
2. Clone repo to `/opt/simops`
3. `cp .env.production.example .env.prod` and fill secrets (`SITE_DOMAIN`, `DB_PASSWORD`, `KEYCLOAK_ADMIN_PASSWORD`, etc.)
4. Set `DOMAIN` in `Caddyfile` → parameterized via `{$DOMAIN}` from `SITE_DOMAIN`
5. Point DNS A record to VPS IP
6. `make prod-up` — checks DB password fingerprint, builds + starts prod stack, waits for backend, runs migrations
7. `make keycloak-redirect URL=https://your-domain.com` — register OIDC redirect URI
8. Configure `scripts/backup.sh` cron (`0 2 * * *`)

```bash
make prod-up       # Build + start production stack
make prod-down     # Stop production stack
make prod-reset    # Full production reset: down + remove volumes + rebuild + migrate + seed
make prod-logs     # Tail production logs
```

Production compose (`docker-compose.prod.yml`): Caddy (TLS termination + static SPA), backend (4 gunicorn workers), db, redis, minio, minio-setup, keycloak + keycloak-db. Only Caddy exposes ports 80/443. Caddy auto-provisions Let's Encrypt certificates.

! Deploy causes ~10-30s downtime. All WebSocket connections drop. Zero-downtime deploy is beyond current scope.

### Ngrok (local-exposed)

```bash
make ngrok-up      # Start local stack + proxy + ngrok tunnel + register Keycloak redirect
make ngrok-down    # Stop ngrok, proxy, and local stack
```

- Requires `~/.ngrok.yml` with tunnel definitions (not in repo)
- `proxy.mjs` routes traffic on port 3000 to local services
- `keycloak-ngrok` queries ngrok API (`localhost:4040/api/tunnels`) for the public URL and registers it with Keycloak as a valid OIDC redirect URI

### Key Makefile targets

| Target | Purpose |
|---|---|
| `local-up` / `local-down` / `local-reset` | Dev stack lifecycle |
| `stack-up` / `stack-down` | Infra containers only (DB, Minio, TiTiler, Keycloak, Redis) |
| `api-up` / `api-down` | Backend container only |
| `migrate` | Alembic migrations inside backend container |
| `seed` | Demo data |
| `prod-up` / `prod-down` / `prod-reset` / `prod-logs` | Production stack lifecycle |
| `prod-check-db-password` | Guard against `DB_PASSWORD` drift |
| `ngrok-up` / `ngrok-down` | Local-exposed mode |
| `sync-from-prod` | Pull prod DB + Minio into local dev |
| `keycloak-redirect URL=...` | Register external URL with Keycloak |
| `verify-ports` | Check `ports.env` agrees with compose files |

## See also

- [Compute](infra/compute.md) — VPS specs, container resource limits
- [Network](infra/network.md) — Caddy routing, Docker DNS
- [Backup/restore runbook](ops/backup-restore.md)
