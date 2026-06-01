# TeacherMarket

TeacherMarket is a self-hostable, Telegram-first catalog and marketplace engine for teacher communities.

OSS v1 helps teachers publish digital learning materials, pass moderation, receive contact requests from buyers, and manage author subscriptions. It does **not** process direct purchases of materials, seller payouts, or protected buyer downloads yet. Those flows are planned for v2.

## Current Scope

- Telegram Mini App frontend built with React and Vite.
- FastAPI backend with PostgreSQL, SQLAlchemy, and Alembic.
- aiogram 3 Telegram bot for onboarding, seller flows, and admin moderation.
- Seller profiles, product catalog, previews, favorites, reviews, reports, and contact requests.
- Author subscription plans with mock payments for local testing and WayForPay support for hosted deployments.
- Local file storage for development and S3/R2-compatible storage for production.
- Admin moderation, audit logs, upload validation, basic rate limiting, and protected admin routes.

Out of scope for OSS v1:

- In-platform material checkout.
- `Order` and `DownloadAccess` models.
- Seller payouts and commission accounting.
- Advanced analytics, promotions, recommendations, and hosted-cloud operations.

## Repository Boundaries

This repository is the public OSS core. It must not contain private production deployment details, real credentials, hosted-cloud operations, seller payout logic, commission accounting, private business roadmaps, internal audit journals, or real teacher/community data.

Use a separate private repository, for example `teachermarket-cloud`, for hosted commercial deployment code, private ops, production configuration, and cloud-only features.

See [Repository boundaries](docs/repository-boundaries.md) before adding deployment, payment, storage, analytics, or hosted-cloud code.

## Repository Layout

```text
apps/api      FastAPI backend
apps/bot      aiogram Telegram bot
apps/webapp   React + Vite Telegram Mini App
docs          OSS, architecture, launch, and self-hosting docs
ops           Generic backup service examples only, no private production config
```

## Quick Start

1. Copy environment defaults:

```bash
cp .env.example .env
```

2. Start PostgreSQL:

```bash
docker compose up -d postgres
```

3. Run API migrations and seed demo data:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Run the bot in another terminal:

```bash
cd apps/bot
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m bot.main
```

5. Run the Mini App:

```bash
cd apps/webapp
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

The Mini App opens at `http://localhost:5173`. Real Telegram authentication requires opening the Mini App from the configured Telegram bot.

## Docker Local Profile

PostgreSQL alone:

```bash
docker compose up -d postgres
```

API, bot, webapp, Postgres, and local storage:

```bash
cp .env.example .env
docker compose --profile app up --build
```

Then run migrations from the API container:

```bash
docker compose --profile app exec api alembic upgrade head
docker compose --profile app exec api python -m app.db.seed
```

## Documentation

- [Implementation plan](docs/implementation-plan.md)
- [Repository boundaries](docs/repository-boundaries.md)
- [Architecture](docs/architecture.md)
- [Self-hosting](docs/self-hosting.md)
- [Roadmap](docs/roadmap.md)
- [Codex guide](docs/codex.md)
- [Community validation](docs/community-validation.md)
- [OpenAI OSS application draft](docs/openai_oss_application.md)
- [OpenAI Codex application notes](docs/openai-application-notes.md)
- [Public release checklist](docs/public-release-checklist.md)
- [Post-implementation audit checklist](docs/post-implementation-audit.md)
- [Demo flow and screenshot checklist](docs/demo-flow.md)
- [Launch preparation checklist](docs/launch_preparation.md)

## API Surface
The current public API covers:

- `POST /auth/telegram`, `POST /auth/bot-user`, `GET /auth/me`
- `GET /products`, `GET /products/{id}`, product create/update/submit for sellers
- `POST /files/upload`, `GET /files/preview/{id}`
- favorites, contact requests, reviews, reports
- seller profile, seller products, contact requests, stats, subscription checkout
- admin product moderation, restore, reports, seller/user controls, subscription plan management
- subscription payment webhooks for mock and WayForPay providers

Production disables `/docs`, `/redoc`, and `/openapi.json`.

## Security Model

- Product files are private by default; public catalog responses expose previews and product metadata, not internal storage keys.
- Preview files are served through `/files/preview/{id}`.
- Admin file downloads require admin JWT auth.
- Telegram Mini App auth verifies `initData` hash and freshness.
- Bot-only user upsert uses `X-Telegram-Bot-Secret`.
- Admin routes check `ADMIN_TELEGRAM_IDS`.
- Uploads validate file kind, extension, MIME type for previews, and size.
- Production startup rejects placeholder secrets, localhost CORS, non-HTTPS app URLs, incomplete WayForPay config, and incomplete S3/R2 config.

See [SECURITY.md](SECURITY.md) for disclosure and supported-version policy.

## Tests

```bash
cd apps/api
python -m unittest discover app/tests -v

cd ../bot
python -m compileall bot

cd ../webapp
npm run build

cd ../..
git diff --check
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md). Good starter issues are listed in [docs/github-starter-issues.md](docs/github-starter-issues.md).

## License

TeacherMarket is licensed under the GNU Affero General Public License v3.0 only. See [LICENSE](LICENSE).
