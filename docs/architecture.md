# Architecture

TeacherMarket uses a simple three-app layout.

```text
Telegram user
  -> aiogram bot
  -> Telegram Mini App
  -> FastAPI API
  -> PostgreSQL
  -> local storage or S3/R2 storage
```

## Apps

### API: `apps/api`

FastAPI application with SQLAlchemy async sessions and Alembic migrations.

Main modules:

- `auth`: Telegram Mini App auth, bot-user upsert, JWT.
- `products`: seller product lifecycle and public catalog.
- `files`: upload validation and preview serving.
- `sellers`: seller profile, products, contact requests, subscriptions, stats.
- `favorites`: saved materials.
- `contact_requests`: buyer-to-author contact flow.
- `reviews`: product feedback.
- `reports`: product complaints.
- `subscriptions`: author subscription checkout and payment webhooks.
- `admin`: moderation, reports, plans, seller/user controls.

### Bot: `apps/bot`

aiogram 3 bot for:

- `/start` and menu entrypoints;
- Mini App launch button;
- seller profile and material submission flow;
- Telegram file upload handoff to API;
- admin moderation callbacks;
- seller subscription and request views.

### Webapp: `apps/webapp`

React + Vite Telegram Mini App for:

- catalog, filters, product detail, favorites;
- contact author CTA;
- seller dashboard;
- product management;
- reviews and reports;
- admin panel inside the profile area.

## Data Model

Core tables include:

- `users`
- `seller_profiles`
- `products`
- `files`
- `product_previews`
- `favorites`
- `contact_requests`
- `reviews`
- `product_reports`
- `product_view_events`
- `subscription_plans`
- `subscriptions`
- `subscription_payments`
- `audit_logs`

OSS v1 intentionally does not include `orders`, `download_access`, payouts, or commission tables.

## Storage

The storage boundary lives in `apps/api/app/services/storage`.

- Local storage is used for development.
- S3-compatible storage supports R2/MinIO-style deployments.
- Public catalog responses expose preview IDs/URLs, not private product file storage keys.
- Admin file download routes are authenticated and admin-only.

## Payments

The payment boundary lives in `apps/api/app/services/payments`.

Implemented providers:

- `mock`: local and closed-beta subscription testing.
- `wayforpay`: author subscription invoices and webhooks.

Payments are for author subscriptions only in v1. Material checkout belongs to v2.

See also:

- `docs/payment-lifecycle.md`
- `docs/subscription-plan-changes.md`
- `docs/one-time-author-upload-fee.md`

## Security Boundaries

- Telegram Mini App identity is verified from signed `initData`.
- API auth uses HMAC-signed JWTs.
- Bot-only user upsert uses `X-Telegram-Bot-Secret`.
- Admin access is based on `ADMIN_TELEGRAM_IDS`.
- Uploads are validated by kind, extension, preview MIME type, and size.
- Production startup rejects unsafe placeholder configuration.
- Audit logs record moderation, subscription, report, product, review, and contact actions.

## Extension Points

Future generic extension points should stay in OSS core only when they are useful for self-hosters:

- payment providers;
- storage providers;
- notification providers;
- optional v2 order/download module.

Hosted-only operations, managed infrastructure, seller payouts, fraud scoring, and private analytics should live outside the public core.
