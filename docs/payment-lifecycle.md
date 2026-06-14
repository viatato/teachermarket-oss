# Payment Intent Lifecycle

TeacherMarket OSS v1 processes payments only for author subscriptions. It does not process purchases of individual materials or payouts to authors.

## Canonical States

- `created`: the local intent exists and may have a provider checkout URL.
- `paid`: a verified success activated or extended the subscription.
- `failed`: the provider reported a failed or declined payment.
- `canceled`: the provider reported a canceled or voided payment.
- `expired`: the checkout expired before payment.

Provider adapters normalize their event names into these states. Unknown states are rejected instead of being written directly to the database.

## Transition Rules

```text
created -> paid | failed | canceled | expired
failed | canceled | expired -> paid
paid -> no other state
```

The late-success transition allows a verified provider success to recover an intent after an earlier terminal-looking notification. A paid intent is never downgraded by a later failure, cancellation, or expiry event.

Repeated events for the current state are idempotent: they do not extend the subscription again or create another audit action. Every event is still signature-checked and validated against the expected provider payment ID, amount, and currency before idempotency is applied.

## Provider Requirements

Every real provider adapter must:

- verify the webhook signature before parsing state;
- use a stable, unique provider payment ID;
- return amount and currency in the local intent's units;
- map provider-specific statuses to the canonical lifecycle;
- avoid logging credentials, raw card data, or unnecessary personal data;
- return an acknowledgement format required by the provider.

The `mock` provider remains intended for local development and controlled beta testing. Its mark-paid endpoint is admin-only.

## One-Time Placements

One-time placements currently activate directly only when `PAYMENT_PROVIDER=mock`, and the feature is disabled by default. A real placement checkout must not reuse that shortcut.

Before enabling placements with a real provider, add a dedicated placement payment intent that follows the same canonical states, signature checks, amount/currency validation, unique provider ID, audit events, and duplicate-webhook rules. Placement payment must remain separate from material checkout and seller payout concepts.
