---
status: open
---

# OOM Kill Cascade on Production VPS

## Question

Why does the production VPS experience repeated OOM kills, and what
mitigations will stabilize it?

## Findings

### System constraints

- VPS RAM: 7.7 GB. Swap: 0 B.
- Container mem_limits total: 9.84 GB (27% overcommit).
- No swap means any transient spike is fatal.

### Pattern 1: Gunicorn workers overshoot 3 GB cgroup

[dmesg evidence]

| Time | Process | anon-rss |
|---|---|---|
| 13:27 | gunicorn | 1344204 kB (~1.28 GB) |
| 13:58 | gunicorn | 1175980 kB (~1.12 GB) |
| 15:03 | gunicorn | 2284812 kB (~2.18 GB) |
| 16:44 | gunicorn | 1400992 kB (~1.34 GB) |
| 16:46 | gunicorn | 2002200 kB (~1.91 GB) |
| 16:55 | gunicorn | 2455228 kB (~2.34 GB) |

- 4 workers × ~1.5 GB avg = ~6 GB; backend cgroup limit is 3 GB.
- No `--max-requests` → workers never recycle.
- Likely causes: GDAL/rasterio buffers, SQLAlchemy identity map,
  pymalloc fragmentation.
- Kill → container restart → 4 fresh workers → growth resumes.

### Pattern 2: Redis kill/restart loop

[dmesg evidence: 20+ kills between 13:42 and 17:01, ~5–15 min cadence]

- Redis has no `maxmemory` configured → never self-evicts.
- Hits 256 MB cgroup ceiling → kernel kills → restart → refill → kill.
- docker stats: 253.1 MiB / 256 MiB (98.85%).
- Every kill drops all pub/sub connections and ephemeral state.

### Container resource allocation

| Service | mem_limit | Current usage |
|---|---|---|
| backend | 3g | 929.8 MiB |
| titiler | 1536m | 1.041 GiB |
| keycloak | 1500m | 618.7 MiB |
| db | 2g | 113 MiB |
| keycloak-db | 512m | 39.87 MiB |
| minio | 512m | 134.8 MiB |
| redis | 256m | 253.1 MiB |
| caddy | 256m | 16.8 MiB |
| **Total** | **~9.84 GB** | **~3.07 GB** |

Current usage is only ~3 GB but workers spike to 2.3 GB each under
load. The limits are allocation caps, not guarantees.

## Mitigations

### Immediate (VPS, no code change)

1. Add 4 GB swap file.
2. Set `vm.swappiness` to 10.

### Short-term (code changes)

1. Create `redis.conf` with `maxmemory 200mb` and
   `maxmemory-policy allkeys-lru`.
2. Increase Redis `mem_limit` to 512m in `docker-compose.prod.yml`.
3. Mount `redis.conf` in compose.
4. Reduce gunicorn workers from 4 to 2.
5. Add `--max-requests 500 --max-requests-jitter 50` to gunicorn CMD.
6. Reduce TiTiler `mem_limit` from 1536m to 1024m.

Rebalanced total: ~7.5 GB (fits within 7.7 GB + swap).

### Investigation

- Profile gunicorn worker RSS growth over hours.
- Audit GDAL/rasterio buffer lifecycle.
- Audit SQLAlchemy session/identity map retention.

## Links

- [Compute](../infra/compute.md)
- [Data Stores](../infra/data-stores.md)
- [Gotchas](../gotchas.md)
- [Build](../build.md)
