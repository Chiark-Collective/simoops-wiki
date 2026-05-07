---
service: backend
summary: "Unauthenticated telemetry sink for frontend auth diagnostic events"
paths: [backend/app/api/routes/diag.py]
flows: []
touches: []
external: []
last_verified_commit: c56ee3d5e04d0143a312d17b22ca262eaa150bd2
---

## Purpose
Accept fire-and-forget `[AUTH-DIAG]` events from the frontend so operators can
grep production logs for intermittent auth-flow bugs that are otherwise
impossible to reproduce locally.

## Interface
- `POST /api/diag/auth-event` — unauthenticated endpoint
- `routes/diag.py::post_auth_event(event, request, credentials)` → 204 No Content; `credentials` is `Optional[HTTPAuthorizationCredentials]` (optional bearer; `auto_error=False`)
- `routes/diag.py::AuthDiagEvent` — Pydantic model: `tag` (str), `data` (dict, default `{}`), `level` (str | None, enum `'log' | 'warn'`)

## Internals
- No auth required — the auth flow itself is being diagnosed; failing-closed would defeat the purpose
- No DB writes — handler only logs via `print(flush=True, file=sys.stdout)` + `logger.warning` (stderr via StreamHandler); same line appears in both stdout and stderr
- Bearer token presence recorded as `auth=True/False` for correlating pre-vs-post-auth events
- Custom `StreamHandler` attached to `simoops.auth_diag` logger at import time (conditional: `if not logger.handlers` to prevent double-registration); ensures events surface in docker logs regardless of root logger config
- Level recorded in payload but not used for dispatch; logger threshold set to `INFO`, call is at `WARNING` to clear the gunicorn/uvicorn default root threshold
- No rate limiting — bounding accepted risk: unauthenticated but only writes log entries; future mitigation: gate behind `core.limiter`

## Gotchas
- `print()` is belt-and-braces alongside `logger.warning()` because the Python logging chain was proven unreliable in prod (alembic root config, gunicorn worker stderr capture)
- Frontend uses `keepalive: true` on the POST so events survive page navigation