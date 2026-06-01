# TeacherMarket — Agent Instructions

Use this file as the working guide for AI coding agents and maintainers contributing to TeacherMarket.

## Project summary

TeacherMarket is a self-hostable Telegram-first catalog for educational materials. It includes:

- FastAPI backend
- aiogram Telegram bot
- React/Vite Telegram Mini App
- PostgreSQL database
- local or S3-compatible file storage
- Telegram Mini App auth
- seller profiles, product catalog, moderation, favorites, contact requests, and subscription plans

The open-source repository should contain the reusable core. Private production infrastructure, real secrets, customer data, and commercial runbooks must not be committed.

## Stack

- API: FastAPI, SQLAlchemy async, Alembic, PostgreSQL
- Bot: aiogram 3
- Webapp: React, Vite, TypeScript
- Storage: local filesystem or S3-compatible provider
- Auth: Telegram Mini App `initData` + JWT
- Payments: mock provider for development; optional provider-specific integrations for deployments

## Repository structure

```text
apps/api      FastAPI backend
apps/bot      Telegram bot
apps/webapp   Telegram Mini App frontend
docs          product, QA, launch, and roadmap docs
```

## Local development

### Environment

```bash
cp .env.example .env
```

Fill in placeholder values. Never commit `.env` or real credentials.

### Database

```bash
docker compose up -d postgres
```

### API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e .
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Bot

```bash
cd apps/bot
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m bot.main
```

### Webapp

```bash
cd apps/webapp
npm install
npm run dev
```

Telegram Web App buttons require HTTPS. For real Mini App auth tests, use a public HTTPS tunnel and update `WEBAPP_URL`, `API_BASE_URL`, `VITE_API_BASE_URL`, and `CORS_ALLOWED_ORIGINS` accordingly.

## Checks before PR

Run the relevant checks for touched areas.

### API tests

```bash
cd apps/api
python -m unittest discover app/tests -v
```

### Bot smoke check

```bash
cd apps/bot
python -m compileall bot
```

### Webapp build

```bash
cd apps/webapp
npm install
npm run build
```

## Coding guidelines

- Keep the app Ukrainian-first in user-facing text unless the surrounding file is explicitly English documentation.
- Keep platform copy clear: TeacherMarket connects teachers and authors; it does not sell individual materials on behalf of authors.
- Do not introduce flows that imply platform-managed payouts unless the product model is intentionally changed.
- Keep secrets in environment variables.
- Do not log Telegram tokens, JWT secrets, payment secrets, signed Telegram `initData`, storage keys, or personally sensitive data.
- Keep admin-only operations guarded by `ADMIN_TELEGRAM_IDS` or a stronger future role system.
- Preserve local development with `PAYMENT_PROVIDER=mock` and `STORAGE_PROVIDER=local`.
- Prefer small, reviewable PRs.

## Security expectations

- Main product files should be private by default.
- Preview assets may be public or signed depending on the deployment, but this must be explicit.
- Upload validation should check size, extension, and content assumptions where possible.
- Telegram Mini App auth must verify signed `initData`, freshness, and clock skew.
- Payment webhooks must verify signatures and be idempotent.
- Never include real production domains, server IPs, server paths, credentials, or private runbooks in public docs.

## Good first contribution areas

- Improve documentation and diagrams.
- Add more backend unit tests.
- Add frontend loading/error/empty states.
- Improve mobile Telegram WebView QA.
- Improve accessibility.
- Add self-hosting guides.
- Improve issue templates and maintainer automation.

## Production / self-hosting

Public OSS docs must not contain private server hosts, SSH usernames, credentials, or provider-specific deployment details. Keep real deployment notes outside the public repository.

Generic deployment guidance lives in `DEPLOY.md` and `docs/self-hosting.md`.

## Важные правила

- **Не коммитить `.env`** — в .gitignore
- **`.env` для API и Bot должны быть синхронизированы** — одинаковые значения на production/self-hosted окружении
- **Статику НЕ класть в private/root-only директории** — web server должен иметь read/execute доступ
- **После смены токена** — обновить в обоих `.env` и перезапустить оба сервиса
- **Перед деплоем** — проверить reverse proxy config, service status, recent service logs
- **Сборка webapp** — `VITE_API_BASE_URL` должен включать `/api` (nginx стриптит префикс)
- **OSS v1 scope** — каталог, профілі авторів, звернення, модерація й авторські підписки; прямі покупки матеріалів, `Order`, `DownloadAccess` і виплати авторам тільки в v2 roadmap

## Полезные команды

```bash
cd apps/api && python -m pytest app/tests
cd apps/api && alembic upgrade head
cd apps/bot && python -m compileall bot
cd apps/webapp && VITE_API_BASE_URL=https://your-domain.example/api npm run build
git diff --check
```

## OSS release docs

- `docs/implementation-plan.md` — актуальний OSS v1 план
- `docs/architecture.md` — карта модулів і межі API/storage/payment
- `docs/self-hosting.md` — локальний запуск і self-hosting
- `docs/roadmap.md` — v0.1 beta та v2 напрями
- `docs/release-gates.md` — automated/manual release checks
- `docs/codex.md` — правила для Codex/contributors
