# Security Policy

TeacherMarket handles teacher accounts, Telegram identity, product files, author subscriptions, and moderation data. Please report security issues privately.

## Supported Versions

Only the current `main` branch and the latest tagged beta release receive security fixes.

## Reporting A Vulnerability

Do not open a public issue for a suspected vulnerability.

Email or privately contact the maintainer with:

- affected component;
- impact;
- reproduction steps;
- logs or screenshots if safe to share;
- whether secrets, files, payments, or admin actions are involved.

Avoid sending raw production secrets, full database dumps, or private teacher materials.

## Sensitive Areas

- Telegram Mini App `initData` verification.
- JWT creation and validation.
- `ADMIN_TELEGRAM_IDS` authorization.
- Bot-only `X-Telegram-Bot-Secret` endpoints.
- Upload validation and private product-file storage.
- Admin file downloads.
- Payment webhook signature verification and idempotency.
- Audit logs for moderation, subscriptions, and admin actions.
- Production env validation and CORS.

## Baseline Expectations

- Product files are not public catalog assets.
- Preview assets may be served publicly or through signed/object-storage policy, depending on deployment.
- Mock payment mark-paid is admin-only.
- WayForPay webhooks must validate provider signatures, amount, currency, and payment identity.
- Production should use HTTPS-only app URLs and specific CORS origins.
