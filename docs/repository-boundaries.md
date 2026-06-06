# Repository Boundaries

TeacherMarket uses an open-core separation model.

This repository, `viatato/teachermarket-oss`, is the public OSS core repository. It must stay self-hostable, safe to publish, and free from private production details.

A separate private repository should be used for the hosted commercial deployment, for example `viatato/teachermarket-cloud`.

---

## Public OSS repository: `teachermarket`

Allowed here:

- Telegram Mini App frontend;
- Telegram bot;
- FastAPI backend;
- PostgreSQL schema and Alembic migrations;
- seller profiles;
- product catalog;
- previews and product metadata;
- contact-author flow;
- favorites, reviews, reports;
- basic moderation and admin tools;
- author subscription flow;
- mock payment provider;
- generic WayForPay adapter code if it contains no private merchant data;
- local storage adapter;
- S3/R2-compatible storage adapter;
- generic Docker/self-hosting examples;
- generic backup examples;
- public-safe documentation;
- public roadmap;
- public issue templates and contribution docs.

The OSS core must be useful on its own and must not become a fake shell for the hosted product.

---

## Private commercial repository: `teachermarket-cloud`

Keep these out of the public OSS repository:

- real production deployment notes;
- real domains, IPs, SSH usernames, and server paths;
- actual nginx/systemd configs for the hosted deployment;
- production `.env` files;
- provider credentials;
- API keys;
- Telegram bot tokens;
- WayForPay merchant secrets;
- Cloudflare/R2 access keys;
- database URLs;
- backup locations for real production data;
- private monitoring/logging setup;
- private admin workflows;
- hosted billing operations;
- commission accounting;
- seller payout logic;
- advanced analytics;
- promotion/ranking/recommendation logic;
- fraud/risk scoring;
- support tooling;
- private business roadmap;
- private teacher/community exports;
- real seller/buyer data;
- real paid educational materials;
- internal audit journals.

---

## Integration rule

The private hosted repository may depend on the OSS core, but the OSS core must not depend on private hosted code.

Recommended direction:

```text
teachermarket-cloud -> imports/uses teachermarket core
teachermarket-oss   -> no dependency on teachermarket-cloud
```

Commercial behavior should be added through configuration, adapters, private packages, or deployment-specific services rather than hardcoded plan checks inside the OSS core.

Avoid this pattern in public OSS code:

```ts
if (plan === "pro") {
  unlockHostedOnlyFeature()
}
```

Prefer extension points:

```ts
export interface PaymentProvider {
  createCheckout(input: CreateCheckoutInput): Promise<CheckoutSession>
  verifyWebhook(input: VerifyWebhookInput): Promise<PaymentWebhookResult>
}
```

Then keep deployment-specific provider configuration and hosted operations private.

---

## Public release rule

Before switching this repository to public:

- complete `docs/public-release-checklist.md`;
- run a secrets scan on the working tree;
- run a secrets scan on git history;
- remove or neutralize internal audit notes;
- remove real deployment notes;
- verify `.env.example` contains only placeholders;
- verify docs use generic domains such as `your-domain.example`;
- verify community screenshots or exports contain no private names, phone numbers, handles, or paid materials;
- verify `docs/community-validation.md` contains only public-safe aggregated data.

If a real secret ever existed in git history, rotate it before making the repository public.

If the existing private repository history contains production operations, customer data, secrets, private server details, or commercial runbooks, do not publish that history. Create a clean public mirror from a reviewed OSS snapshot instead, following `docs/public-release-checklist.md`.
