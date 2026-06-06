# One-Time Author Upload Fee Proposal

## Status

Design proposal for GitHub issue #5. This is not an implementation plan for OSS v1 unless self-hoster demand is validated.

## Problem

Teacher feedback raised a possible self-hosting need: some communities may prefer a one-time author payment tied to uploading or publishing materials instead of, or alongside, recurring author subscriptions.

The feature must preserve the OSS v1 product boundary. TeacherMarket remains a catalog where buyers browse materials and contact authors. It must not become a direct material checkout, protected buyer download, seller payout, or commission system.

## Goals

- Let self-hosters optionally charge authors once for the right to upload or publish materials.
- Keep the option disabled by default.
- Keep buyer flows unchanged: browse, favorite, review, report, and contact author.
- Reuse the existing payment-provider boundary where possible.
- Make the feature understandable in public OSS docs without production details or secrets.

## Proposed Model

### Product boundary

The fee is charged to authors, not buyers. A successful fee payment grants permission to submit one or more author materials for moderation. It does not grant any buyer access to product files.

Product pages continue to show catalog metadata, previews, author-stated price information, and the contact-author CTA. `price_amount` remains informational and does not trigger platform-managed purchase logic.

### Configuration

Self-hosters could choose one of these modes:

- `disabled`: default OSS v1 behavior; author upload fees are not shown.
- `per_product`: each submitted product requires one paid upload pass.
- `credit_pack`: one payment grants a fixed number of upload credits.

Subscriptions can continue to exist separately. A self-hoster may choose subscriptions only, one-time upload fees only, both, or neither.

### Data model sketch

Potential tables or equivalent records:

- `author_upload_fee_plans`: public name, amount, currency, upload credits granted, active flag, sort order.
- `author_upload_fee_payments`: seller profile, optional product, plan, provider, provider reference, amount, currency, status, idempotency key, timestamps.
- `author_upload_credits`: seller profile, source payment, remaining credits, optional expiration, timestamps.
- `audit_logs`: record fee plan changes, payment status changes, and credit consumption.

Payment statuses should mirror the subscription payment lifecycle where practical: pending, paid, failed, canceled, refunded, expired.

### Author flow

1. Author creates or edits a draft material.
2. If the selected self-hosting mode requires a fee, the API checks whether the seller has an active subscription or available upload credit.
3. If payment is needed, the author is sent to the configured provider payment page.
4. A verified webhook marks the author payment as paid and grants the upload credit.
5. Submitting the material for moderation consumes the required credit.
6. Admin moderation remains unchanged: approve, reject, hide, restore.

If a product is rejected, the self-hoster must decide whether the credit is spent on submission or only on approval. The safer default is to spend it on submission, with an admin-only manual credit adjustment for mistakes.

### Payment providers

The existing `mock` provider can support local testing. Other providers should be added through the same generic payment-provider interface used by author subscriptions.

Provider records must use generic identifiers and idempotent webhook handling. Public OSS docs should include placeholder configuration only and must not include merchant accounts, secrets, domains, server paths, or private runbooks.

## Non-Goals

- No buyer payment for individual materials.
- No direct material checkout.
- No protected buyer download access.
- No `Order` or `DownloadAccess` model in OSS v1.
- No seller payout, commission, balance, or settlement system.
- No hosted-cloud billing operations in the public repository.
- No provider-specific production settings, credentials, domains, IPs, or private deployment steps.
- No guarantee that an upload fee means a material will be approved by moderators.

## Risks

- Users may confuse an author upload fee with buying a material. Product and payment copy must clearly say the fee is for authors publishing catalog listings.
- Payment-provider support may duplicate subscription logic unless the shared payment boundary is kept small and generic.
- Refunds and rejected materials can create support expectations. Self-hosters need a documented policy before enabling the feature.
- Credit consumption rules can feel unfair if authors pay for rejected submissions. Admin adjustment tooling may be needed.
- More payment modes increase migration complexity for communities already using subscriptions.
- Moderation abuse remains possible if paid authors submit low-quality or prohibited materials.
- Local tax, invoicing, receipt, and consumer-protection obligations vary by self-hoster and jurisdiction.
- Adding this too early could blur the v1 boundary and delay stronger catalog, moderation, and contact-author reliability.

## Recommendation

Keep OSS v1 focused on the existing contact-author catalog and author subscription model. Treat one-time author upload fees as an optional self-hosting extension candidate after community validation.

If implemented later, start with `per_product` mode, mock-provider tests, idempotent webhook handling, and clear UI copy that says the payment is for author publishing access only.
