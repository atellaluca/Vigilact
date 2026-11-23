# SQLite reference storage: backup and recovery

The Python reference server uses a single SQLite database. The Go observer uses
a different, single-process JSON snapshot store. **Neither implementation is
production-grade HA storage.**

## Consistent Python backup

Do not assume that copying a live SQLite file with `cp` will capture a
transactionally consistent database. Use SQLite's online backup API:

```bash
python scripts/backup_sqlite.py \
  --db ./vigilact.sqlite3 \
  --output ./vigilact-backup-2026-11-23.sqlite3
```

The helper refuses to overwrite an existing backup, checks SQLite integrity and
restricts the backup file to owner read/write permissions where supported.
Keep backups encrypted and off-host. Credentials are configured separately and
**are not** included in the database backup.

## Recovery rehearsal

1. Stop the reference observer; make a separate copy of its current database.
2. Restore the backup to a new file path.
3. Start an isolated reference observer pointed at that path.
4. Verify `/readyz`, inspect one known contract and confirm the outbox cursor.
5. Do not run two writers against the same database or Go snapshot concurrently.

Restore/restart can evaluate overdue contracts; this is expected. Consumers
must handle replays at-least-once. Never assume the observer can retrospectively
infer operations that occurred while it was offline.

This operational helper is **not a normative part of the protocol**.
