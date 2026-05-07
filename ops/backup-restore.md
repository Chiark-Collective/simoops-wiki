---
symptom: "data loss or recovery required"
related_flows: []
related_infra: [compute, data-stores]
related_external: [postgis]
last_verified_commit: c56ee3d5
---

# Backup and Restore

## Detect

- `pg_dump` failure in `backup.sh` log
- Missing files in `/opt/simops/backups/` older than 14 days
- Minio COGs absent after VPS disk failure
- `pending_storage_deletes` backlog in `/api/health/ready` response

## Diagnose

1. Check backup directory: `ls -la /opt/simops/backups/`
2. Verify latest dump integrity: `pg_dump --list <latest.sql> | head`
3. Check cron execution: `grep backup /var/log/syslog` or `crontab -l`
4. Check Minio bucket: `mc ls simoops-cogs` (requires `mc` CLI configured)
5. Verify VPS disk: `df -h /opt/simops`

## Mitigate

### PostgreSQL restore

```bash
# On VPS
docker compose -f docker-compose.prod.yml exec db psql -U simoops -d simoops -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='simoops';"
docker compose -f docker-compose.prod.yml exec db dropdb -U simoops simoops
docker compose -f docker-compose.prod.yml exec db createdb -U simoops simoops
cat /opt/simops/backups/<dump.sql> | docker compose -f docker-compose.prod.yml exec -T db psql -U simoops simoops
```

### Minio restore

No automated backup exists. If COGs are lost:
1. Check if `sync-from-prod.sh` was run recently — local dev may have a copy
2. Re-upload COGs manually via `mc mirror` or Minio console
3. Re-run source imports if originals are available

### Backup setup (new VPS)

```bash
# Add to crontab
crontab -e
0 2 * * * /opt/simops/scripts/backup.sh
```

`backup.sh` performs: `pg_dump` → verify dump → prune files older than 14 days. Optional `rclone copy` for offsite is commented out — enable once `rclone` is configured.

### Sync prod data to local dev

```bash
make sync-from-prod          # Pull prod DB + Minio into local
make sync-from-prod -- --dry-run  # Preview without writing
```

SSH alias `simops` must be configured. Script recreates local DB, runs migrations, promotes demo admin, and mirrors Minio COGs.

## Failure modes

- **No Minio backup** — uploaded site maps and floor plans have no scheduled backup; only PostgreSQL is covered
- **No offsite backup** — `rclone` line in `backup.sh` is commented out; VPS disk failure loses both data and backups
- **Keycloak sessions lost on restart** — realm re-imported from `realm-export.json`; all active sessions invalidated, users must re-authenticate
- **DB password fingerprint mismatch** — `prod-check-db-password.sh` blocks `prod-up` if `DB_PASSWORD` changed since volume initialization; restoring from dump does not change the password
