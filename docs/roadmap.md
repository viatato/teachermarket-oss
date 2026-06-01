# Roadmap

## v0.1.0-beta: OSS v1 Foundation

- Public AGPL-3.0 repository.
- FastAPI, aiogram, and React/Vite setup documented.
- Seller profiles, product catalog, previews, favorites, reviews, reports, and contact requests.
- Product moderation and audit logs.
- Author subscription plans with mock and WayForPay providers.
- Local and S3/R2-compatible storage.
- GitHub CI and contributor docs.
- Community validation document.

## Closed Beta Release Gate

- Live Telegram `/start` smoke.
- Mini App auth with real Telegram `initData`.
- Seller upload and submit.
- Admin approve, reject, hide, restore.
- Buyer favorite, review, report, and contact author.
- Mock subscription idempotency.
- Wrong payment signature rejection.
- Private product-file access check.
- Backup restore test.
- R2 bucket privacy verification.

## v0.2: Self-Hosting Hardening

- More integration tests around product lifecycle and contact requests.
- Docker production example.
- Optional MinIO example.
- Stronger backup/restore docs.
- Dependency scanning and security workflow.
- Better observability guidance.

## v0.3: Marketplace Optional Module Design

Design only until validated:

- `Order`
- `DownloadAccess`
- manual material payment confirmation;
- protected buyer download URLs;
- refund/cancellation states;
- seller payout and commission model boundaries.

This work must remain optional so the current catalog/contact-author model stays useful for communities that do payments outside the platform.

## Hosted/Cloud Track

Hosted TeacherMarket features should extend the core instead of forking it:

- managed hosting;
- automatic updates;
- managed storage;
- operational dashboards;
- advanced analytics;
- promotions;
- recommendation/ranking;
- support tooling;
- fraud/risk workflows.

Hosted-only code should not add hardcoded `pro` checks throughout the OSS core.
