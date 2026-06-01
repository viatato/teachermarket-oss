# Self-Hosting

This guide describes a basic self-hosted TeacherMarket deployment. It assumes PostgreSQL, one API process, one bot process, and static webapp hosting.

## Requirements

- Python 3.11 or newer.
- Node.js 22 or newer.
- PostgreSQL 16.
- A Telegram bot token.
- HTTPS domain for Telegram Mini App production use.
- Local disk storage or S3/R2-compatible object storage.

## Local Docker Profile

Start all development services:

```bash
cp .env.example .env
docker compose --profile app up --build
```

Run migrations and seed data:

```bash
docker compose --profile app exec api alembic upgrade head
docker compose --profile app exec api python -m app.db.seed
```

Open:

- API: `http://localhost:8000/health`
- Webapp: `http://localhost:5173`

## Manual Local Setup

```bash
cp .env.example .env
docker compose up -d postgres

cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd apps/bot
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m bot.main
```

```bash
cd apps/webapp
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Environment

Production must set:

```text
APP_ENV=production
API_BASE_URL=https://your-domain.example
WEBAPP_URL=https://your-domain.example
CORS_ALLOWED_ORIGINS=https://your-domain.example
DATABASE_URL=postgresql+asyncpg://...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_SECRET=...
ADMIN_TELEGRAM_IDS=...
JWT_SECRET=...
PAYMENT_WEBHOOK_SECRET=...
```

When `APP_ENV=production`, the API rejects placeholder secrets, non-HTTPS app URLs, localhost CORS, incomplete WayForPay config, and incomplete S3/R2 config.

## Telegram Setup

In BotFather:

- create or reuse a bot;
- set the Mini App/menu button URL to your HTTPS webapp URL;
- set bot description and commands;
- ensure the Mini App domain matches `WEBAPP_URL`.

The Mini App must be opened through Telegram to provide real `window.Telegram.WebApp.initData`.

## Storage

Local development:

```text
STORAGE_PROVIDER=local
LOCAL_STORAGE_PATH=/tmp/teachermarket_storage
```

S3/R2 production:

```text
STORAGE_PROVIDER=r2
S3_ENDPOINT_URL=https://...
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_BUCKET=teachermarket
S3_REGION=auto
```

Keep product files private. Preview delivery can be public or signed depending on bucket policy and deployment needs.

## Subscription Payments

Local/closed beta:

```text
PAYMENT_PROVIDER=mock
PAYMENT_WEBHOOK_SECRET=...
```

WayForPay:

```text
PAYMENT_PROVIDER=wayforpay
WAYFORPAY_API_URL=https://api.wayforpay.com/api
WAYFORPAY_MERCHANT_ACCOUNT=...
WAYFORPAY_SECRET_KEY=...
WAYFORPAY_MERCHANT_DOMAIN=your-domain.example
```

Payments are for author subscriptions only. TeacherMarket OSS v1 does not process material purchases or payouts.

## Static Webapp Deployment

Build with the public API prefix used by your reverse proxy:

```bash
cd apps/webapp
VITE_API_BASE_URL=https://your-domain.example/api npm run build
```

Serve `apps/webapp/dist/` from your web server.

## Backups

The `ops/` directory contains a systemd timer and shell script example for PostgreSQL backups. Before public launch:

- enable daily backup;
- keep at least 14 days of retention;
- test restore into staging or local PostgreSQL;
- document where backups live.
