# TeacherMarket v0.1.0-beta

First public beta release of TeacherMarket OSS core.

TeacherMarket is a self-hostable Telegram-first catalog and marketplace engine for teacher communities.

## What's Included

- FastAPI backend with PostgreSQL
- aiogram Telegram bot
- React/Vite Telegram Mini App
- PostgreSQL schema and migrations
- Seller profiles
- Product catalog with search, filters, and pagination
- Image previews for materials
- Favorites for buyers
- Reviews and reports
- Contact requests (buyer writes to author directly)
- Admin moderation (approve, reject, request changes, hide, restore)
- Audit logs for moderation actions
- Author subscription plans (mock and WayForPay providers)
- Local and S3/R2-compatible storage
- Docker Compose local profile (API, bot, webapp, Postgres)
- CI workflow, issue/PR templates, labels, milestones
- OSS documentation (contributing, security, architecture, self-hosting, roadmap)
- Repository boundary docs (clear OSS core vs commercial/hosted layer)

## Not Included in OSS v1

- In-platform checkout for individual materials
- Seller payouts
- Commission accounting
- Protected buyer downloads
- Hosted-cloud private operations
- Real teacher community data

## Before Using in Production

Self-hosters should review:

- `docs/self-hosting.md`
- `docs/release-gates.md`
- `SECURITY.md`
- `.env.example`

## Known Beta Requirements

- Telegram Mini App requires HTTPS for real auth (`initData` validation)
- Production deployments must configure secure secrets, CORS, storage, backups, and payment webhooks
- Community validation is still in progress
- Manual Telegram tap-test must be completed by the owner before the repo is made public

## License

AGPL-3.0 only