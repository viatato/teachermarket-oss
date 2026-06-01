# TeacherMarket OSS v1 Implementation Plan

## Summary

TeacherMarket OSS v1 is the current FastAPI, aiogram, and React/Vite project adapted into a self-hostable, Telegram-first catalog engine for teacher communities.

Teachers can publish educational materials, manage seller profiles, upload product files and previews, pass moderation, receive contact requests, and pay for an author subscription. Buyers can browse the catalog, save materials, review products, report problems, and contact authors.

Direct material checkout, seller payouts, `Order`, and `DownloadAccess` are not part of v1. They are documented as v2 work so the OSS core stays honest and useful instead of promising flows it does not currently implement.

## Scope

Included in OSS v1:

- Telegram Mini App catalog.
- Telegram bot launch, seller, and moderation flows.
- FastAPI backend.
- PostgreSQL schema and Alembic migrations.
- Seller profiles and product lifecycle.
- Product previews and private product-file storage.
- Favorites, contact requests, reviews, reports, product views, and seller stats.
- Author subscription plans, mock payment provider, and WayForPay provider.
- Admin moderation and audit logs.
- Local development and self-hosting docs.
- GitHub CI, issue templates, and contributor docs.

Deferred to v2:

- Material purchase orders.
- Manual order approval.
- Protected buyer download access.
- Seller payouts and commission accounting.
- Advanced analytics, promotions, recommendations, and hosted-cloud operations.

## Implementation Phases

### Phase 1: OSS Packaging

- Keep the current repo and app layout.
- Add AGPL-3.0-only license metadata.
- Maintain English-first contributor docs.
- Keep Ukrainian launch/community docs for first users and teachers.
- Add GitHub issue templates, PR template, starter issue backlog, labels, milestones, and CI.

### Phase 2: Self-Hosting

- Document fresh-clone setup with Postgres, migrations, seed data, API, bot, and webapp.
- Keep local storage as the default development adapter.
- Document R2/S3-compatible storage for production.
- Document Telegram BotFather setup.
- Document mock subscription payments and WayForPay production payment settings.

### Phase 3: Product Stabilization

- Keep buyer CTA as contact author.
- Treat `price_amount` as author-stated product price information, not a platform checkout.
- Keep product files private and expose only previews through public routes.
- Finish manual Telegram smoke before public release.
- Add visible service rules, complaint policy, and onboarding copy for authors.

### Phase 4: Hardening

- Validate production settings at startup.
- Keep RBAC checks on admin and mock payment routes.
- Keep upload extension, size, and preview MIME validation.
- Keep payment webhook verification and idempotency.
- Add tests around security-sensitive service rules.

### Phase 5: Launch

- Run community validation in the teacher audience.
- Convert feedback into public issues.
- Verify production smoke, backup restore, private-file access, and R2 bucket policy.
- Tag `v0.1.0-beta` only after CI is green and manual release gates are complete.

## Acceptance Criteria

- A contributor can run the app locally from the docs.
- CI checks API tests, migrations, bot import/compile, webapp build, and Docker builds.
- Docs do not promise direct in-platform material purchase for v1.
- The public catalog never exposes private product files.
- Admin and payment-sensitive routes remain protected.
- Public release notes clearly identify remaining manual gates.

## Assumptions

- No backend migration to Node.js or TypeScript.
- No `packages/*` monorepo migration for v1.
- TeacherMarket Cloud and private hosted operations stay outside OSS core.
- Material checkout is designed later as an optional v2 module.
