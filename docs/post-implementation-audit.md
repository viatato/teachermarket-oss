# Post-Implementation Audit Checklist

Use this checklist after major OSS readiness work and before publishing the repository or applying to OpenAI Codex for Open Source.

## Public Repository Safety

The public repo must not contain:

- real Telegram bot tokens;
- OpenAI or third-party API keys;
- payment provider secrets;
- webhook secrets;
- real database URLs;
- production `.env` files;
- SSH keys or cloud credentials;
- real seller or buyer data;
- private teacher materials;
- private moderation notes;
- customer support messages;
- private business calculations;
- private hosted/cloud roadmap;
- production admin credentials.

Allowed:

- `.env.example`;
- fake/demo credentials;
- local development config;
- seed demo data;
- fake seller profiles and fake products;
- mock/test payment provider docs;
- generic architecture, roadmap, and self-hosting docs.

Suggested scan commands:

```bash
git grep -i "token"
git grep -i "secret"
git grep -i "password"
git grep -i "api_key"
git grep -i "apikey"
git grep -i "bot_token"
git grep -i "database_url"
git grep -i "webhook"
git grep -i "private"
git grep -i "prod"
git grep -i ".env"
```

If a real secret was ever committed, rotate it before publishing even if the file was deleted later.

## Open-Core Separation

Public OSS core includes:

- Mini App frontend;
- Telegram bot;
- backend API;
- database schema and migrations;
- seller profiles;
- product catalog;
- file upload;
- contact-author flow;
- basic moderation and admin panel;
- author subscription payment providers;
- storage provider adapters;
- local/self-hosting setup;
- documentation, security policy, contributor guide.

Private hosted/cloud code should contain:

- hosted infrastructure;
- production deployment secrets;
- seller payouts;
- commission accounting;
- advanced analytics;
- paid promotion;
- ranking/recommendations;
- fraud/risk scoring;
- support tooling;
- internal operations.

Avoid commercial lock-in logic in OSS core. Prefer interfaces and extension points.

## Functional OSS v1 Check

Buyer/contact flow:

- user can open the bot;
- user can open the Telegram Mini App;
- user can browse the product catalog;
- user can open a product page;
- user can favorite a product;
- user can create a contact request;
- user can review or report a product where allowed.

Seller flow:

- user can create a seller profile;
- seller can upload product files and previews;
- seller can create and edit a product draft;
- seller can submit product for moderation;
- seller can see product status and contact requests;
- seller can view author subscription status.

Admin/moderator flow:

- admin access is restricted by `ADMIN_TELEGRAM_IDS`;
- admin can see pending products;
- admin can approve/reject/request changes/hide/restore;
- admin can review reports;
- admin can manage plans and seller/user controls;
- moderation actions are logged.

Material order checkout, protected buyer downloads, and seller payouts are v2 checks, not OSS v1 release blockers.

## Local Development Check

- `README.md` explains local setup.
- `.env.example` exists and is safe.
- Docker Compose has Postgres and app profile docs.
- Alembic migrations work.
- Seed data works.
- API starts locally.
- Bot starts locally with a real Telegram token.
- Webapp starts locally.
- Mock author subscription flow works.

Actual verification commands:

```bash
cd apps/api && python -m pytest app/tests
cd apps/api && alembic upgrade head
cd apps/bot && python -m compileall bot
cd apps/webapp && npm run build
git diff --check
```

## Documentation Check

Required documents:

- `README.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `CHANGELOG.md`
- `docs/architecture.md`
- `docs/self-hosting.md`
- `docs/roadmap.md`
- `docs/community-validation.md`
- `docs/openai-application-notes.md`

## Security Check

- Secrets are not committed.
- `.env.example` is safe.
- Admin routes are protected.
- File uploads are validated and size-limited.
- Product files are not exposed by public catalog routes.
- Payment confirmation is not publicly forgeable.
- Webhooks verify signatures and payment identity.
- Rate limiting exists on sensitive endpoints.
- Moderation/admin actions are logged.
- `SECURITY.md` explains private vulnerability reporting.
- Dependency scanning is enabled or tracked as a public issue.

## GitHub Readiness Check

- Public repository exists.
- License is added.
- Project description is clear.
- Repository topics/tags are set.
- Issue templates exist.
- Pull request template exists.
- GitHub Actions CI exists.
- Labels and milestones are defined.
- At least 10-20 starter issues exist.
- Some issues are marked `good first issue`.
- Some issues are marked `codex-friendly`.
- Roadmap is visible.
- First release is tagged only after release gates pass.

## Community Validation Check

- Teacher community size is documented honestly.
- Poll was posted.
- Poll results are summarized.
- Beta tester interest is collected.
- Seller interest is collected.
- Buyer/user interest is collected.
- Feedback is converted into GitHub issues.
- `docs/community-validation.md` is updated.

Do not publish private names, phone numbers, Telegram handles, or private messages without permission.

## Final Go / No-Go

Go only when:

- no secrets or private user data are in repo;
- open-source and commercial boundaries are clear;
- local setup works;
- OSS v1 flow works;
- README and AGENTS are useful;
- security policy exists;
- self-hosting docs exist;
- issues/milestones exist;
- community validation is documented;
- OpenAI application text is prepared;
- maintainer role is clear;
- repository looks active and serious.
