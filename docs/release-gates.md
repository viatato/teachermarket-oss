# v0.2.0-beta Release Gates

This is the live checklist for the next beta. Completed `v0.1.0-beta` evidence remains in Git history; it must not be reused as proof that a new release candidate passed.

Record the candidate commit, test date, operator, and hosted deployment separately. Do not add private domains, server paths, user identities, credentials, or raw Telegram `initData` to this public repository.

## Automated

- [ ] `cd apps/api && python -m unittest discover app/tests -v`
- [ ] `cd apps/api && alembic heads` reports exactly one head.
- [ ] `cd apps/api && alembic upgrade head` succeeds against a disposable database.
- [ ] `cd apps/bot && python -m compileall bot`
- [ ] `cd apps/webapp && npm ci && npm run build`
- [ ] `python3 scripts/release_readiness.py --skip-commands`
- [ ] `git diff --check`
- [ ] `gitleaks dir --redact --no-banner .`
- [ ] `gitleaks git --log-opts=HEAD --redact --no-banner`
- [ ] GitHub Actions CI is green on the exact release candidate.

The release-readiness script is read-only and can perform negative HTTP checks against a supplied API URL. The history scan is deliberately limited to commits reachable from the candidate `HEAD`, so unrelated private remotes or local branches do not create false release blockers. It does not replace migration, storage, backup, or real Telegram-client testing.

## Public Repository Safety

- [ ] The candidate contains only reusable OSS code and public-safe documentation.
- [ ] No `.env`, production config, private runbook, real domain/IP/path, dump, customer data, teacher material, payment payload, or private screenshot is present.
- [ ] [Service rules](service-rules.md), [complaint policy](complaint-policy.md), and [author onboarding](author-onboarding.md) match the implemented OSS v1 model.
- [ ] Direct material checkout, buyer downloads, payouts, and hosted operations remain outside OSS v1.
- [ ] Any real credential found in any source repository has been rotated; scan output and secret values are not committed.

## Release Identity

- [ ] The deployment sets `RELEASE_ID` to the release tag or immutable commit/build identifier.
- [ ] `GET /health` returns the expected `release`, `environment`, and database status.
- [ ] The running `release` exactly matches the candidate tested below.

## Manual Telegram Smoke

- [ ] Telegram `/start` opens the expected Ukrainian menu.
- [ ] Mini App opens from Telegram on iOS and Android.
- [ ] `POST /auth/telegram` accepts real signed Telegram `initData`; raw `initData` is not saved in evidence.
- [ ] Favorites sync to the authenticated buyer.
- [ ] Buyer can create a contact request and the seller can see it.
- [ ] Seller can create a profile, see service rules, upload previews and a private product file, and submit a material.
- [ ] Admin can approve, reject, request changes, hide, restore, and resolve a report.
- [ ] Buyer can create, edit, and delete their own review and report a material.
- [ ] The author onboarding checklist is completed with a test author or approved beta author.

## Payments And Visibility

- [ ] OSS v1 copy never claims that TeacherMarket sells individual materials or pays authors out.
- [ ] The beta deployment uses mock/manual subscription activation or an explicitly approved provider configuration; unintended live checkout is unavailable.
- [ ] Non-admin users cannot mark mock subscription or placement payments paid.
- [ ] Wrong webhook signatures fail and duplicate valid webhooks are idempotent.
- [ ] Product visibility correctly follows the enabled free tier, subscription, grace-period, and optional one-time-placement rules.
- [ ] Disabled subscription, placement, review, and report modules return the documented unavailable behavior.

## Security And Infrastructure

- [ ] Main product files are not publicly accessible; preview delivery follows the deployment's documented policy.
- [ ] Non-admin users cannot access moderation or private-file routes.
- [ ] Backup freshness and retention meet the deployment policy (recommended minimum: 14 days).
- [ ] A current backup restores successfully into a disposable non-production database.
- [ ] S3/R2/MinIO private-object access is verified with unsigned requests.
- [ ] CORS, HTTPS, rate limits, error monitoring, and uptime monitoring match the hosted deployment's risk profile.

## Release Approval

- [ ] No open P0/P1 issue affects authentication, roles, private files, payments, or data integrity.
- [ ] Release notes describe user-visible changes and known beta limits without private operational details.
- [ ] The candidate commit is merged to public `main` before the tag is created.
- [ ] `v0.2.0-beta` is tagged from that exact commit only after every applicable gate above is complete.
