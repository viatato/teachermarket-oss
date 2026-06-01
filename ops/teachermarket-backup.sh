#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/srv/teachermarket/api}
ENV_FILE="$APP_DIR/.env"
BACKUP_ROOT=${BACKUP_ROOT:-/srv/teachermarket/backups}
RETENTION_DAYS=14
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE="$BACKUP_ROOT/logs/backup_$TIMESTAMP.log"

mkdir -p "$BACKUP_ROOT/db" "$BACKUP_ROOT/storage" "$BACKUP_ROOT/logs"

get_env() {
  local key="$1"
  grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | tail -n 1 | cut -d= -f2- | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
}

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" | tee -a "$LOG_FILE"
}

DATABASE_URL="$(get_env DATABASE_URL)"
if [[ -z "$DATABASE_URL" ]]; then
  log "DATABASE_URL missing; aborting database backup."
  exit 1
fi

PG_DUMP_URL="${DATABASE_URL/postgresql+asyncpg:/postgresql:}"
DB_TARGET="$BACKUP_ROOT/db/teachermarket_$TIMESTAMP.sql.gz"
log "Starting PostgreSQL backup."
pg_dump "$PG_DUMP_URL" | gzip -9 > "$DB_TARGET"
chmod 600 "$DB_TARGET"
gzip -t "$DB_TARGET"
log "Database backup written: $DB_TARGET"

STORAGE_PROVIDER="$(get_env STORAGE_PROVIDER)"
STORAGE_PROVIDER="${STORAGE_PROVIDER:-local}"
if [[ "$STORAGE_PROVIDER" == "local" ]]; then
  LOCAL_STORAGE_PATH="$(get_env LOCAL_STORAGE_PATH)"
  LOCAL_STORAGE_PATH="${LOCAL_STORAGE_PATH:-/tmp/teachermarket_storage}"
  if [[ -d "$LOCAL_STORAGE_PATH" ]]; then
    STORAGE_TARGET="$BACKUP_ROOT/storage/teachermarket_storage_$TIMESTAMP.tar.gz"
    tar -C "$(dirname "$LOCAL_STORAGE_PATH")" -czf "$STORAGE_TARGET" "$(basename "$LOCAL_STORAGE_PATH")"
    chmod 600 "$STORAGE_TARGET"
    log "Local storage backup written: $STORAGE_TARGET"
  else
    log "Local storage path not present: $LOCAL_STORAGE_PATH"
  fi
else
  S3_BUCKET="$(get_env S3_BUCKET)"
  MANIFEST="$BACKUP_ROOT/storage/storage_manifest_$TIMESTAMP.txt"
  {
    printf 'timestamp=%s\n' "$TIMESTAMP"
    printf 'storage_provider=%s\n' "$STORAGE_PROVIDER"
    printf 's3_bucket=%s\n' "$S3_BUCKET"
    printf 'note=%s\n' 'Object storage is external; verify bucket retention/lifecycle in provider console.'
  } > "$MANIFEST"
  chmod 600 "$MANIFEST"
  log "Storage manifest written for provider: $STORAGE_PROVIDER"
fi

find "$BACKUP_ROOT/db" -type f -name '*.sql.gz' -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_ROOT/storage" -type f \( -name '*.tar.gz' -o -name 'storage_manifest_*.txt' \) -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_ROOT/logs" -type f -name 'backup_*.log' -mtime +"$RETENTION_DAYS" -delete
log "Retention cleanup complete: ${RETENTION_DAYS} days."
