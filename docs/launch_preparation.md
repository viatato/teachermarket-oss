# TeacherMarket: closed beta launch preparation

This document is a generic operational checklist for a closed beta or self-hosted deployment. It must stay safe for a public OSS repository.

TeacherMarket OSS v1 does not process direct payments for individual materials and does not pay out sellers. It helps authors publish materials, pass moderation, receive contact requests, and manage author subscriptions. Service monetization is based on author subscriptions.

Do not add private server hosts, SSH usernames, real domains, credentials, production IPs, private paths, or private provider account details to this file. Keep real deployment notes outside the public repository.

---

## 1. Production env checklist

Required variables:

```text
APP_ENV=production
APP_NAME=teachermarket
API_BASE_URL=https://your-domain.example/api
WEBAPP_URL=https://your-domain.example
DATABASE_URL=postgresql+asyncpg://...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_BOT_USERNAME=...
TELEGRAM_WEBHOOK_SECRET=...
ADMIN_TELEGRAM_IDS=...
JWT_SECRET=...
CORS_ALLOWED_ORIGINS=https://your-domain.example
PAYMENT_PROVIDER=mock або real provider
PAYMENT_WEBHOOK_SECRET=...
WAYFORPAY_MERCHANT_ACCOUNT=...
WAYFORPAY_SECRET_KEY=...
WAYFORPAY_MERCHANT_DOMAIN=your-domain.example
DEFAULT_FREE_PRODUCT_LIMIT=3
PRO_AUTHOR_PRODUCT_LIMIT=50
```

Requirements:

- `JWT_SECRET`, `TELEGRAM_WEBHOOK_SECRET`, and `PAYMENT_WEBHOOK_SECRET` must be long random values.
- `CORS_ALLOWED_ORIGINS` must contain only the production Mini App domain.
- `ADMIN_TELEGRAM_IDS` must contain only real admin Telegram IDs for the deployment.
- `PAYMENT_PROVIDER=mock` is acceptable only for development or closed testing without real charges.
- For closed QA, `WEBAPP_URL` must point to the actual HTTPS Mini App domain for that deployment.
- Production webapp builds must use `VITE_API_BASE_URL=https://your-domain.example/api` or the equivalent deployment API URL.
- For `PAYMENT_PROVIDER=wayforpay`, fill merchant account, secret key, and production domain only in the private server `.env`.
- Secrets must never be committed to the repository or written to public logs.

---

## 2. Domain, Telegram, and webhooks

Prepare:

- Production domain for the API.
- Production domain for the Mini App.
- HTTPS certificate for both domains.
- Telegram BotFather:
  - bot username;
  - bot description;
  - menu button to the Mini App URL;
  - Mini App domain allowlist.
- Bot webhook or polling mode:
  - production API endpoint if webhooks are used;
  - secret header or secret path if webhooks are used;
  - health monitoring.
- Telegram login for closed QA:
  - open the Mini App through the Telegram bot/WebApp button to receive real `window.Telegram.WebApp.initData`;
  - a normal browser without Telegram is not a valid auth test and may only work in demo/fallback mode;
  - backend must accept only signed and fresh `initData`, create/update the user, and issue JWT;
  - frontend must use JWT for favorites, contact requests, seller dashboard, and subscription checkout.
- Payment webhook:
  - URL `POST /subscription-payments/webhook/{provider}`;
  - signature secret;
  - wrong signature test;
  - duplicate webhook test.

Go/no-go:

- [ ] Mini App opens from Telegram on the deployment domain.
- [ ] Bot `/start` shows menu.
- [ ] Admin menu is available only to admins.
- [ ] Admin Mini App panel supports moderation, restore, tariff edit/toggle, reports, seller/user controls, and bulk hide/restore.
- [ ] Payment webhook rejects wrong signatures.

---

## 3. Database and backups

Before launch:

- [ ] Create production PostgreSQL database on the selected host.
- [ ] Run Alembic migrations.
- [ ] Seed subscription plans such as Free, Pro monthly, and Pro yearly or the current deployment plan set.
- [ ] Verify that `subscription_plans` contains the expected active plans.
- [ ] Configure automated backups at least once per day.
- [ ] Configure backup retention for at least 14 days.
- [ ] Test restore against a staging or local database.

Backup checklist:

```text
[ ] Daily backup configured
[ ] Backup encryption enabled
[ ] Restore command documented
[ ] Restore tested
[ ] Admin knows where backups live
```

---

## 4. Storage

MVP can run with local storage, but production should use object storage.

Prepare:

- [ ] Choose storage provider: local, S3-compatible, R2, or MinIO.
- [ ] Create private bucket/container if object storage is used.
- [ ] Disable public read for main product files.
- [ ] Decide whether preview assets are public or signed.
- [ ] Verify upload limits:
  - product file max size;
  - preview max size;
  - allowed extensions.

Security rule:

- Main product files must not be accessible through public URLs.
- Public catalog shows only previews and metadata.

---

## 5. Service rules

### Allowed content

- Original educational materials.
- Worksheets, tests, speaking cards, presentations, lesson plans, games, templates.
- Materials the author has rights to publish.
- Materials with previews that honestly show the content.

### Not allowed

- Third-party materials without permission.
- Pirated copies of textbooks, courses, worksheets, or presentations.
- Materials containing students' personal data.
- Discriminatory, hateful, pornographic, or illegal content.
- Files with malware, executable payloads, or dangerous archives.
- Materials that mislead buyers about content or price.

### Service role

TeacherMarket:

- shows the material catalog;
- accepts author applications;
- performs moderation;
- lets buyers contact authors;
- charges only for author subscription to the service.

TeacherMarket does not:

- accept payment for individual materials;
- guarantee the transaction between buyer and author;
- pay authors out;
- become a party to the purchase between teachers.

### Subscription terms

- Free plan gives a base material limit.
- Pro plan increases material limits.
- Subscription affects the ability to publish materials in the catalog.
- Subscription does not guarantee sales or contact volume.
- Rule violations may result in hidden materials or blocked profiles.

### Complaint policy

Buyer or author can complain about:

- copyright infringement;
- mismatch between material and description;
- unacceptable content;
- fraud in off-platform communication.

Minimum process:

```text
1. Receive complaint.
2. Record material, author, complainant, and problem description.
3. Temporarily hide material if risk is high.
4. Ask author for explanation.
5. Decide: keep, request changes, hide, or block.
```

### Author responsibility

Author is responsible for:

- rights to the material;
- truthful description;
- file quality;
- buyer communication;
- service-rule compliance.

---

## 6. First authors and materials

Target before launch:

- 10-20 first authors.
- 30-50 starter materials.
- At least 3-5 material categories.
- At least 2-3 levels or audiences.

Author onboarding:

```text
1. Explain that the service connects buyers with authors.
2. Ask author to create a Telegram username.
3. Help author complete seller profile.
4. Provide a product-description template.
5. Explain preview requirements.
6. Upload first material.
7. Pass moderation.
8. Verify that CTA “Contact author” opens chat.
```

Material description template:

```text
Title:
Audience:
Level:
What is inside:
How to use it in a lesson:
File format:
Activity duration:
```

---

## 7. Manual launch QA

Before launch, test manually:

```text
[ ] Bot /start opens menu
[ ] Mini App opens from Telegram
[ ] POST /auth/telegram returns JWT for real Telegram Mini App initData
[ ] GET /auth/me returns the current Telegram user with Bearer token
[ ] Opening Mini App outside Telegram shows explicit demo/fallback mode, not a real login
[ ] Buyer can open catalog
[ ] Buyer can filter catalog
[ ] Buyer can open product page
[ ] Buyer can save a material and see favorites synced to Telegram account
[ ] Buyer can click “Contact author”
[ ] Contact request is stored
[ ] Seller sees contact request
[ ] Seller dashboard shows real data after Telegram login
[ ] Seller dashboard shows stats: views, contacts, reviews, rating
[ ] Seller can create profile
[ ] Seller can upload file and previews
[ ] Seller can submit material
[ ] Seller can edit rejected/draft material in Mini App
[ ] Seller can delete own material with warning for published
[ ] Admin can approve material
[ ] Published material appears in catalog
[ ] Admin can hide material
[ ] Admin can restore hidden material
[ ] Admin can edit/toggle subscription plans in Mini App
[ ] Admin can bulk hide/restore selected materials
[ ] Admin can suspend/activate seller and block/unblock user
[ ] Buyer can create, edit, and delete own review
[ ] Recently viewed list stores product snapshots and can be cleared
[ ] Non-admin user cannot access moderation actions
[ ] Seller can see subscription status
[ ] Mock subscription checkout works in selected mode
[ ] Mock mark-paid endpoint without admin auth returns 401
[ ] Duplicate payment webhook does not extend subscription twice
[ ] Wrong payment signature fails
[ ] Invalid or expired Telegram initData returns 401
[ ] Main product file is not publicly accessible
[ ] Backups are configured and restore was tested
```

---

## 8. Launch decision

Go:

- [ ] Mini App opens from Telegram.
- [ ] Bot `/start` shows menu.
- [ ] Admins can moderate.
- [ ] Admins can manage plans, reports, seller/user controls, and bulk actions.
- [ ] First authors can publish materials.
- [ ] Authors can edit, re-submit, and delete own materials.
- [ ] Buyers can contact authors.
- [ ] Buyers can leave, edit, and delete reviews.
- [ ] Subscription flow works in selected mode.
- [ ] Backups are configured and restore tested.
- [ ] Rules are visible to authors.

No-go:

- Mini App does not open in Telegram.
- Telegram Mini App login does not issue JWT for real `initData`.
- Admin cannot moderate.
- Private product file is public.
- Contact request is not stored.
- Non-admin can moderate or mark mock payments as paid.
- Expired or invalid Telegram `initData` is accepted.
- Payment webhook accepts wrong signature.
- No database backup.
