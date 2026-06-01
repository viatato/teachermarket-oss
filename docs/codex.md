# Codex Guide

TeacherMarket is a good fit for Codex because the maintainer workload spans code review, security hardening, tests, documentation, issue triage, and release QA.

## Project Rules

- Keep OSS v1 self-hostable.
- Do not add material checkout, payouts, or hosted-cloud-only behavior unless the issue explicitly scopes a v2 design.
- Preserve the current stack: FastAPI, SQLAlchemy/Alembic, aiogram, React/Vite.
- Update docs when changing setup, env, architecture, or security-sensitive behavior.
- Never commit secrets, `.env`, production dumps, private teacher materials, or raw payment credentials.

## Useful Commands

```bash
cd apps/api && python -m pytest app/tests
cd apps/api && alembic upgrade head
cd apps/bot && python -m compileall bot
cd apps/webapp && npm run build
git diff --check
```

## Review Priorities

1. Private product files must stay private.
2. Admin routes must stay admin-only.
3. Mock payment mark-paid must stay admin-only.
4. Webhooks must verify signatures and payment identity.
5. Telegram Mini App auth must verify signed and fresh `initData`.
6. Self-hosting docs must match the real repo.
7. Public docs must not promise material purchases in OSS v1.

## Good Codex Tasks

- Add focused tests for service rules.
- Improve docs and onboarding.
- Triage beta feedback into issues.
- Review migration safety.
- Harden upload validation.
- Improve CI and release checks.
- Draft release notes.
- Validate public issue templates.

## OpenAI OSS Application Notes

TeacherMarket can be presented as open-source infrastructure for teacher communities. The strongest proof points are:

- existing teacher community size;
- beta tester and seller interest;
- first product examples;
- feedback converted into public issues;
- clear self-hosting path;
- visible maintainer workload around security, docs, tests, and user feedback.
