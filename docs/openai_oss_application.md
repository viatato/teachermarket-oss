# TeacherMarket — OpenAI OSS Application Draft

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

TeacherMarket provides a reusable OSS core for these communities.

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

## Application narrative draft

TeacherMarket is a self-hostable Telegram-first catalog for educational materials, built for teacher communities that already live inside Telegram. It helps authors publish materials, pass moderation, receive contact requests, and organize materials by language, level, category, and audience.

The project is open source because small schools, tutor communities, and teacher groups repeatedly need this infrastructure but often cannot afford custom platforms. TeacherMarket gives them a reusable core they can self-host and adapt.

The project is currently in early beta and open-source preparation. The core MVP already includes a FastAPI backend, aiogram bot, React/Vite Telegram Mini App, PostgreSQL schema, Telegram auth, seller profiles, catalog, favorites, contact requests, moderation, file upload support, and subscription plan logic.

OpenAI Codex would help the project move from a working MVP to a maintainable open-source project by assisting with tests, PR review, documentation, issue triage, security hardening, and contributor onboarding. The maintainer plans to use Codex as part of the regular maintenance workflow for reviewing changes around Telegram auth, file storage, uploads, payment webhooks, and frontend/mobile QA.
