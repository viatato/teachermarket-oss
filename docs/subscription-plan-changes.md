# Subscription Plan Changes

TeacherMarket OSS v1 uses author subscriptions to control author publishing
limits. It does not process direct material checkout, protected buyer downloads,
seller payouts, or commission accounting.

## Current Model

Authors choose an active paid plan through subscription checkout. When a payment
is marked paid by the mock provider or confirmed by a real provider webhook, the
backend activates or extends the seller subscription.

If the seller already has an active paid subscription, the paid time is not
discarded. The new plan becomes the active plan and the new duration is appended
to the current `expires_at` value. If no active paid subscription exists, the
new subscription starts at the payment confirmation time.

This keeps plan changes conservative for OSS self-hosters:

- upgrades do not shorten the already paid period;
- downgrades do not delete remaining paid time;
- repeated mock mark-paid calls are idempotent and do not extend twice;
- expired subscriptions are ignored before a new paid period is created.

## Admin Overrides

Admins can manually activate or extend an author subscription. Manual activation
uses the same conservative rule: extend from the current future expiration when
one exists, otherwise start from now.

## Non-Goals

- No direct buyer checkout for individual materials in OSS v1.
- No protected buyer download entitlement.
- No seller payout or commission state machine.
- No hosted-only plan behavior hardcoded into the OSS core.

## Testing Expectations

Plan-change regressions should cover:

- an active paid subscription changing to a different plan without shortening
  the current paid period;
- an expired seller state creating a fresh paid subscription;
- duplicate mock payment confirmation returning the already-paid payment without
  extending the subscription again.
