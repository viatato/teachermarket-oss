# Public Release Gates

These checks must be complete before tagging `v0.1.0-beta`.

## Automated

- [ ] `cd apps/api && python -m pytest app/tests`
- [ ] `cd apps/api && alembic upgrade head`
- [ ] `cd apps/bot && python -m compileall bot`
- [ ] `cd apps/webapp && npm run build`
- [ ] `git diff --check`
- [ ] GitHub Actions CI green

## Public Repository Safety

- [ ] `docs/public-release-checklist.md` completed.
- [ ] Secret scan commands from `docs/post-implementation-audit.md` reviewed.
- [ ] Commit history checked for secrets before making the repo public.
- [ ] Any previously committed real secret rotated.
- [ ] No real seller, buyer, teacher-community, moderation, support, payment, cloud, or admin data included.
- [ ] No private TeacherMarket Cloud or TeacherBoard business logic included.
- [ ] If old private/commercial history is unsafe for publication, publish only through the clean public mirror flow in `docs/public-release-checklist.md`.

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

- [ ] Main product file is not publicly accessible.
- [ ] Non-admin cannot access admin moderation routes.
- [ ] Non-admin cannot mark mock payments paid.
- [ ] Wrong payment webhook signature fails.
- [ ] Duplicate payment webhook does not extend subscription twice.
- [ ] Daily backup timer is active.
- [ ] Backup restore tested into staging/local database.
- [ ] R2/private bucket policy verified in provider console.
- [ ] No secrets in repo, docs, GitHub Actions, screenshots, or release notes.

## GitHub Readiness

- [ ] Repository is public.
- [ ] Repository description and topics/tags are set.
- [ ] Issue templates render correctly.
- [ ] Pull request template renders correctly.
- [ ] Labels from `.github/labels.yml` are created in GitHub.
- [ ] Milestones from `.github/milestones.md` are created in GitHub.
- [ ] Starter issues from `docs/github-starter-issues.md` are created.
- [ ] At least some starter issues are labeled `good first issue`.
- [ ] At least some starter issues are labeled `codex-friendly`.
- [ ] First release is tagged only after this checklist passes.

## Community

- [ ] Teacher poll run.
- [ ] Problems/pain-points poll summarized.
- [ ] Beta tester interest collected.
- [ ] Cloud beta tester count documented as an aggregate.
- [ ] Seller interest collected.
- [ ] Buyer/user interest collected.
- [ ] Teacher community size documented honestly.
- [ ] Feedback themes summarized in `docs/community-validation.md`.
- [ ] Public issues created from non-private feedback.
- [ ] Raw poll exports and tester identities kept outside the public repository.

## OpenAI Codex For OSS Application

- [ ] `docs/openai_oss_application.md` updated with current facts.
- [ ] `docs/openai-application-notes.md` updated with current facts.
- [ ] Application text says the project is early/beta if still in beta.
- [ ] Application text does not overclaim adoption.
- [ ] Maintainer role is clear.
- [ ] Codex use cases are specific: review, triage, tests, security, migrations, docs, releases.
- [ ] Community proof points are linked or summarized.
- [ ] GitHub profile and repository visibility are public before submission.
- [ ] OpenAI Organization ID is prepared.
- [ ] Form answers fit the current character limits.

## Local Agent Guardrails

- [ ] Resolve or waive any local agent-memory verification guardrails before push, PR, publication, or release tagging.
