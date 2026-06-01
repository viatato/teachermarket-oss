# Changelog

## 0.1.0-beta (2026-06-01)

First public beta release of TeacherMarket OSS core.

- AGPL-3.0-only licensed.
- Added public README, contributing guide, security policy, code of conduct, and changelog.
- Added architecture, self-hosting, roadmap, repository-boundaries, release-gates, and community-validation docs.
- Added OpenAI OSS/Codex application notes.
- Added Docker Compose app profile for API, bot, webapp, Postgres, and local storage.
- Added production runtime settings validation for placeholder secrets, HTTPS URLs, CORS, WayForPay, and S3/R2 config.
- Added GitHub templates (issues, PR, labels, milestones) and CI workflow.
- Added starter issues document.
- Removed private deployment details, production domains, and production environment files from public docs.
- API: 26 tests, bot: 23 modules compiled, webapp: build passes.
- Gitleaks history scan: clean (1 false positive — CSS palette description).
- Code review: 17 admin route guards, Telegram initData HMAC validation, payment webhook idempotency, file access control, all verified.
