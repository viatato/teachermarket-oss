# Contributing

Thanks for helping TeacherMarket become useful open-source infrastructure for teacher communities.

## Development Setup

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

In separate terminals:

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

## Picking Work

- Start with issues labeled `good first issue`, `documentation`, or `codex-friendly`.
- Security-sensitive work should also follow [SECURITY.md](SECURITY.md).
- Ask before adding direct material checkout, payouts, or hosted-cloud-only behavior to OSS core.

## Branches And Commits

- Use focused branches, for example `feature/self-hosting-docs` or `fix/upload-validation`.
- Keep commits scoped and descriptive.
- Do not commit `.env`, credentials, production dumps, or private business data.

## Pull Request Checklist

Every PR should answer:

- What changed?
- Why was it needed?
- How was it tested?
- Does it affect security?
- Does it affect self-hosting?
- Does it require documentation updates?

Run the relevant checks:

```bash
cd apps/api && python -m pytest app/tests
cd apps/api && alembic upgrade head
cd apps/bot && python -m compileall bot
cd apps/webapp && npm run build
git diff --check
```

## Code Style

- Keep the current stack: FastAPI, SQLAlchemy/Alembic, aiogram, React/Vite.
- Prefer small service functions with explicit authorization checks.
- Keep adapter boundaries for storage and payments.
- Do not expose private product files, storage keys, internal payment payloads, or admin-only data through public APIs.
