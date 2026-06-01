# Deployment Notes

TeacherMarket OSS does not include private production infrastructure details. Use this file as a generic self-hosting checklist and keep provider-specific hosts, usernames, SSH aliases, credentials, and private nginx/systemd notes outside the public repository.

For full setup details, see `docs/self-hosting.md`.

## Build Webapp

Set `VITE_API_BASE_URL` to the public API URL used by your reverse proxy:

```bash
cd apps/webapp
VITE_API_BASE_URL=https://your-domain.example/api npm run build
```

Serve `apps/webapp/dist/` from your static web server.

## API Service

Example systemd shape:

```ini
[Unit]
Description=TeacherMarket API
After=network-online.target

[Service]
WorkingDirectory=/srv/teachermarket/api
EnvironmentFile=/srv/teachermarket/api/.env
ExecStart=/srv/teachermarket/api/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8020
Restart=always

[Install]
WantedBy=multi-user.target
```

Before starting production:

```bash
cd apps/api
alembic upgrade head
python -m app.db.seed
```

## Bot Service

Example systemd shape:

```ini
[Unit]
Description=TeacherMarket Bot
After=network-online.target

[Service]
WorkingDirectory=/srv/teachermarket/bot
EnvironmentFile=/srv/teachermarket/bot/.env
ExecStart=/srv/teachermarket/bot/.venv/bin/python -m bot.main
Restart=always

[Install]
WantedBy=multi-user.target
```

## Reverse Proxy

Recommended:

- HTTPS for the Mini App domain.
- `/api/` proxied to API.
- static webapp served from a non-root web directory.
- production API docs disabled with `APP_ENV=production`.
- HSTS and common security headers at the proxy layer.

## Pre-Deploy Checklist

- [ ] `.env` exists only on the server and is not committed.
- [ ] `APP_ENV=production`.
- [ ] `API_BASE_URL`, `WEBAPP_URL`, and `CORS_ALLOWED_ORIGINS` use HTTPS.
- [ ] `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `JWT_SECRET`, and `PAYMENT_WEBHOOK_SECRET` are real random values.
- [ ] R2/S3 values are complete if `STORAGE_PROVIDER=r2` or `s3`.
- [ ] WayForPay values are complete if `PAYMENT_PROVIDER=wayforpay`.
- [ ] Migrations pass.
- [ ] Backup is taken before deploy.
- [ ] Reverse proxy config test passes.

## Post-Deploy Smoke

- [ ] `GET /health` returns `database: ok`.
- [ ] Root HTML and static JS/CSS load.
- [ ] Production docs routes return 404.
- [ ] Unauthenticated admin routes return 401 or 403.
- [ ] Bot process is active.
- [ ] Telegram `/start` works.
- [ ] Mini App auth works with real Telegram `initData`.
- [ ] Main product files are not publicly reachable.
