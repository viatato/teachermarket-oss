# TeacherMarket Ops

## Self-Hosted Backups

TeacherMarket can use `teachermarket-backup.timer` on a self-hosted server.

- Schedule: daily at `03:15` server time.
- Script: `/srv/teachermarket/scripts/backup.sh`.
- DB backups: `/srv/teachermarket/backups/db/teachermarket_*.sql.gz`.
- Storage backups:
  - `STORAGE_PROVIDER=local`: compressed local storage tarball.
  - `STORAGE_PROVIDER=s3`/R2: manifest file only; verify R2 lifecycle/retention in the provider console.
- Retention: 14 days.

Manual run:

```bash
ssh user@your-server "systemctl start teachermarket-backup.service"
```

Restore a DB backup into a target database:

```bash
gunzip -c /srv/teachermarket/backups/db/teachermarket_YYYYMMDDTHHMMSSZ.sql.gz \
  | psql "postgresql://USER:PASSWORD@HOST:PORT/DBNAME"
```

For production restore, stop `teachermarket-api.service` and `teachermarket-bot.service` first, restore into the intended database, then restart both services and check `/health`.
