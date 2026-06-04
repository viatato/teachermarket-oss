# TeacherMarket — OpenAI OSS Application Draft

This draft is written for the OpenAI Codex for Open Source application. It should stay honest: TeacherMarket is an early OSS core with active teacher-community validation and a started hosted beta, not a widely adopted public platform yet.

## Project summary

TeacherMarket is a self-hostable Telegram-first catalog for teacher communities to publish and discover educational materials.

It is designed for language teachers, tutor communities, small schools, education creators, and Telegram-based teacher groups.

## Open-source value

Many teacher communities already work inside Telegram. Materials are often shared manually through chats, folders, spreadsheets, and private messages. This creates repeated problems:

- no structured catalog
- no moderation flow
- no author profiles
- no filtering by language, level, category, or audience
- no clear way to contact authors
- no reusable self-hosted foundation for small education communities

TeacherMarket provides a reusable OSS core for these communities: catalog, author profile, moderation, contact-author, upload, and subscription infrastructure that can be adapted by self-hosted education communities.

Current validation signals:

- Telegram teacher community with 1,461 members;
- TeacherMarket product-interest poll with 11 responses;
- broader problems-and-pain-points poll with 33 responses;
- 8 hosted/cloud beta testers;
- hosted beta has started;
- early OSS release-readiness work with CI, release gates, security docs, and starter issues.

Aggregate poll counts and public-safe evidence are summarized in `docs/community-validation.md`.

## Current OSS core

- FastAPI backend
- aiogram Telegram bot
- React/Vite Telegram Mini App
- PostgreSQL schema and migrations
- seller profiles
- material catalog
- product detail pages
- favorites
- contact requests
- admin moderation
- subscription plan model
- local development setup
- mock payment provider
- local or S3-compatible storage

## Private/commercial layer boundary

The public repository should contain the reusable core. Private deployments may add custom branding, hosting, analytics, commercial operations, payment-provider configuration, and private author onboarding.

## Why Codex helps

Codex can support the maintainer workflow through:

- pull request review
- test generation
- issue triage
- documentation updates
- release checklist work
- migration review
- Telegram Mini App QA
- hardening auth, uploads, storage, and payment webhooks
- refactoring repeated bot/API/frontend logic
- preparing contributor-friendly issues

These are ongoing maintainer responsibilities, not one-off product development tasks. The highest-risk areas for review are Telegram Mini App auth, file uploads, private storage, payment webhooks, moderation actions, migrations, and mobile Mini App QA.

## Proposed maintainer workflow

1. New issue is opened.
2. Maintainer classifies it as bug, docs, feature, QA, or security-sensitive.
3. Codex helps propose a small implementation plan.
4. Codex helps prepare or review a focused PR.
5. CI runs backend tests, bot smoke checks, and webapp build.
6. Maintainer reviews and merges.

## Near-term OSS milestones

- Public-safe README and documentation.
- License, contributing guide, security policy, roadmap.
- CI checks.
- Issue and PR templates.
- Public demo seed data.
- Clear self-hosting guide.
- First `good first issue` tasks.
- Closed beta QA with real teacher users.
- Public-safe community validation summary.
- Public feedback issues derived from teacher validation: [#6 automoderation](https://github.com/viatato/teachermarket-oss/issues/6), [#5 one-time author upload fee option for self-hosters](https://github.com/viatato/teachermarket-oss/issues/5), [#4 tariff changes](https://github.com/viatato/teachermarket-oss/issues/4), and [#7 material complaint handling](https://github.com/viatato/teachermarket-oss/issues/7).
- First public beta release candidate or `v0.1.0-beta` tag after release gates pass.

## Application Form Drafts

### Why does this repository qualify?

```text
TeacherMarket is a self-hostable Telegram-first catalog engine for teacher communities. It is built around a 1,461-member teacher community, 44 poll responses, and 8 cloud beta testers. The OSS core addresses validated needs for catalog, moderation, author profiles, direct contact, and reusable self-hosted infrastructure.
```

### How will you use API credits?

```text
I will use API credits for core OSS maintenance: PR review, issue triage from teacher beta feedback, test generation for FastAPI/bot/webapp flows, release checklist automation, documentation updates, and security review around Telegram auth, uploads, storage, moderation, and payment webhooks.
```

### Anything else we should know?

```text
TeacherMarket is intentionally scoped: OSS v1 focuses on catalog, author profiles, contact requests, moderation, file uploads, and subscriptions. Direct material checkout, protected downloads, seller payouts, and commission accounting are future v2 work, so the public repository stays honest and reusable for self-hosted education communities.
```

## Longer Application Narrative

TeacherMarket is a self-hostable Telegram-first catalog for educational materials, built for teacher communities that already live inside Telegram. It helps authors publish materials, pass moderation, receive contact requests, and organize materials by language, level, category, and audience.

The project is open source because small schools, tutor communities, and teacher groups repeatedly need this infrastructure but often cannot afford custom platforms. TeacherMarket gives them a reusable core they can self-host and adapt.

The project is currently in hosted beta and open-source preparation. The core MVP already includes a FastAPI backend, aiogram bot, React/Vite Telegram Mini App, PostgreSQL schema, Telegram auth, seller profiles, catalog, favorites, contact requests, moderation, file upload support, and subscription plan logic.

OpenAI Codex would help the project move from a working MVP to a maintainable open-source project by assisting with tests, PR review, documentation, issue triage, security hardening, and contributor onboarding. The maintainer plans to use Codex as part of the regular maintenance workflow for reviewing changes around Telegram auth, file storage, uploads, payment webhooks, and frontend/mobile QA.

## Submission Readiness Checklist

- [ ] GitHub profile is public.
- [ ] `viatato/teachermarket` repository is public.
- [ ] `docs/community-validation.md` contains aggregate poll and beta tester counts.
- [ ] Public feedback issues labeled `community-feedback` are created from non-private beta feedback.
- [ ] Starter issues from `docs/github-starter-issues.md` are visible.
- [ ] GitHub Actions are green on the release branch.
- [ ] `docs/release-gates.md` is current.
- [ ] OpenAI Organization ID is ready.
