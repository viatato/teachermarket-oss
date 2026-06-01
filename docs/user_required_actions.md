# Maintainer Action Checklist

This public checklist captures maintainer-owned release tasks without private deployment details. Keep real domains, IP addresses, SSH usernames, server paths, credentials, provider account data, private tester lists, and customer data outside this repository.

## Local QA

- [ ] Start PostgreSQL with `docker compose up -d postgres`.
- [ ] Run API migrations and seed demo data from `apps/api`.
- [ ] Run the bot from `apps/bot`.
- [ ] Run the Mini App from `apps/webapp`.
- [ ] Verify `/health` returns an OK database status.

## Telegram Mini App QA

Real Telegram Mini App auth requires opening the app from Telegram, not directly from a normal browser.

- [ ] `/start` works in the configured Telegram bot.
- [ ] The Mini App opens from the bot button.
- [ ] `POST /auth/telegram` accepts real signed Telegram `initData`.
- [ ] `GET /auth/me` returns the current Telegram user with a bearer token.
- [ ] Favorites persist for the authenticated user.
- [ ] Contact requests can be created.
- [ ] Seller dashboard flows work for the authenticated seller.
- [ ] Admin-only controls are visible only to configured admins.

Use a temporary HTTPS tunnel or a self-hosted HTTPS environment for Telegram QA. Document only generic setup steps in this repository.

## Closed Beta QA

- [ ] Invite only testers who understand this is a beta.
- [ ] Ask testers not to upload real paid materials unless they own the rights.
- [ ] Ask testers not to share screenshots with personal data in public issues.
- [ ] Keep private tester identities, phone numbers, Telegram handles, and support notes outside the public repository.
- [ ] Summarize only public-safe aggregate feedback in `docs/community-validation.md`.

## Release Prep

- [ ] Complete `docs/public-release-checklist.md`.
- [ ] Complete `docs/release-gates.md`.
- [ ] Verify `docs/openai_oss_application.md` is current and honest about beta status.
- [ ] Confirm release notes contain no private production details.
