# Public Release Gates

These checks must be complete before tagging `v0.1.0-beta`.

## Automated

- [x] `cd apps/api && python -m unittest discover app/tests -v`
- [x] `cd apps/api && alembic upgrade head`
- [x] `cd apps/bot && python -m compileall bot`
- [x] `cd apps/webapp && npm run build`
- [x] `git diff --check`
- [x] `python3 scripts/release_readiness.py --skip-commands`
- [x] GitHub Actions CI green

The release readiness script is a read-only summary helper for local or
production smoke signals. It does not replace the manual Telegram-client smoke
test because real Mini App auth depends on Telegram-provided `initData`.

## Public Repository Safety

- [x] `docs/public-release-checklist.md` completed.
- [x] Secret scan commands from `docs/post-implementation-audit.md` reviewed.
- [x] Commit history checked before publication; the public repository uses a clean reviewed mirror history.
- [x] Previously exposed production credentials were rotated outside the public repository.
- [x] No real seller, buyer, teacher-community, moderation, support, payment, cloud, or admin data included.
- [x] No private TeacherMarket Cloud or TeacherBoard business logic included.
- [x] Unsafe private/commercial history was excluded through the clean public mirror flow.

## Manual Telegram Smoke

- [ ] Telegram `/start` opens the correct menu.
- [ ] Mini App opens from Telegram.
- [ ] `POST /auth/telegram` accepts real signed `initData`.
- [ ] Favorites sync to the authenticated user.
- [ ] Buyer can create a contact request.
- [ ] Seller receives/sees the contact request.
- [ ] Seller can upload previews and a product file.
- [ ] Seller can submit a material.
- [ ] Admin can approve, reject, request changes, hide, and restore.
- [ ] Buyer can create, edit, and delete own review.
- [ ] Buyer can report a product.

## Security And Infrastructure

- [x] Main product file is not publicly accessible.
- [x] Non-admin cannot access admin moderation routes.
- [x] Non-admin cannot mark mock payments paid.
- [x] Wrong payment webhook signature fails.
- [x] Duplicate payment webhook does not extend subscription twice.
- [x] Daily backup timer is active in the hosted reference deployment.
- [x] Backup restore tested into a non-production database.
- [x] R2/private bucket runtime access verified with unsigned object requests.
- [ ] R2 lifecycle/retention policy verified in the provider console.
- [x] No secrets in the public repo, docs, GitHub Actions, screenshots, or release notes.

## GitHub Readiness

- [x] Repository is public.
- [x] Repository description and topics/tags are set.
- [x] Issue templates are present in `.github/ISSUE_TEMPLATE/`.
- [x] Pull request template is present.
- [x] Labels from `.github/labels.yml` are created in GitHub.
- [x] Milestones from `.github/milestones.md` are created in GitHub.
- [x] Starter issues from `docs/github-starter-issues.md` are created.
- [x] Starter issues include `good first issue` labels.
- [x] Starter issues include `codex-friendly` labels.
- [ ] First release is tagged only after this checklist passes.

## Community

- [x] Teacher poll run.
- [x] Problems/pain-points poll summarized.
- [x] Beta tester interest collected.
- [x] Cloud beta tester count documented as an aggregate.
- [x] Seller interest collected.
- [x] Buyer/user interest collected.
- [x] Teacher community size documented honestly.
- [x] Feedback themes summarized in `docs/community-validation.md`.
- [x] Public issues created from non-private feedback.
- [x] Raw poll exports and tester identities kept outside the public repository.

## OpenAI Codex For OSS Application

- [x] `docs/openai_oss_application.md` updated with current facts.
- [x] `docs/openai-application-notes.md` updated with current facts.
- [x] Application text says the project is early/beta if still in beta.
- [x] Application text does not overclaim adoption.
- [x] Maintainer role is clear.
- [x] Codex use cases are specific: review, triage, tests, security, migrations, docs, releases.
- [x] Community proof points are linked or summarized.
- [x] GitHub profile and repository visibility are public before submission.
- [ ] OpenAI Organization ID is prepared.
- [x] Form answers fit the current character limits.
- [ ] Application submitted by the maintainer with personal account details and terms acceptance.

## Local Agent Guardrails

- [x] Local agent-memory verification guardrails resolved before current publication work.
