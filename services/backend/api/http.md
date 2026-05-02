---
service: backend
channel: http
---

# HTTP API

## Entity CRUD

| Route | Method | Auth | Flow | Notes |
|---|---|---|---|---|
| `/api/tokens/` | GET/POST | Bearer | entity_creation | Site-scoped |
| `/api/zones/` | GET/POST | Bearer | entity_creation | Polygon geometry |
| `/api/fences/` | GET/POST | Bearer | entity_creation | Safety boundaries |
| `/api/sections/` | GET/POST | Bearer | entity_creation | Phased areas |
| `/api/plants/` | GET/POST | Bearer | entity_creation | Equipment assets |
| `/api/workers/` | GET/POST | Bearer | entity_creation | Personnel |

## Planning

| Route | Method | Auth | Flow | Notes |
|---|---|---|---|---|
| `/api/planning-cycles/` | GET/POST | Bearer | planning_cycle | Create / list cycles |
| `/api/planning-cycles/{id}/import-baseline` | POST | Bearer | planning_cycle | Shadow baseline into cycle |
| `/api/planning-cycles/{id}/actualize` | POST | Bearer | planning_cycle | Fork planned → actual |
| `/api/planning-cycles/{id}/submit` | POST | Bearer | planning_cycle | Submit for review |

## Clash

| Route | Method | Auth | Flow | Notes |
|---|---|---|---|---|
| `/api/clashes/` | GET | Bearer | clash_detect_and_resolve | List computed clashes |
| `/api/clash-rules/` | GET/POST | Bearer | clash_detect_and_resolve | Rule management |
| `/api/clash-rules/{id}/evaluate` | POST | Bearer | clash_detect_and_resolve | On-demand evaluation |

## Reports

| Route | Method | Auth | Flow | Notes |
|---|---|---|---|---|
| `/api/reports/` | GET/POST | Bearer | report_export | Session management |
| `/api/reports/{id}/export/pdf` | POST | Bearer | report_export | PDF generation |
| `/api/reports/{id}/export/docx` | POST | Bearer | report_export | DOCX generation |

## Admin

| Route | Method | Auth | Flow | Notes |
|---|---|---|---|---|
| `/api/sites/` | GET/POST | Bearer | — | Site management |
| `/api/users/` | GET | Bearer | — | User listing |
| `/api/health` | GET | None | — | Liveness probe |

## Geometry

| Route | Method | Auth | Flow | Notes |
|---|---|---|---|---|
| `/api/geometry-operations/cut` | POST | Bearer | entity_creation | Polygon cutting |
| `/api/geometry-operations/vertex` | POST | Bearer | entity_creation | Vertex OT edits |

## Imports

| Route | Method | Auth | Flow | Notes |
|---|---|---|---|---|
| `/api/bulk-import/` | POST | Bearer | — | CAD / CSV bulk ingest |
| `/api/bundle-import/` | POST | Bearer | — | Floor plan bundle |
| `/api/permit-import/` | POST | Bearer | — | Permit data ingest |
