# OpenAI Codex For Open Source Application Notes

This document is draft material for a future OpenAI Codex for Open Source application. Keep it honest: TeacherMarket is an early OSS core around an existing teacher ecosystem, not a widely adopted public platform yet.

## Short Project Description

TeacherMarket is an open-source, self-hostable, Telegram-first catalog engine for teacher communities. It helps teachers publish educational materials, manage seller profiles, pass moderation, receive contact requests from buyers, and run a catalog inside Telegram through a bot and Mini App.

OSS v1 focuses on catalog, contact-author, moderation, file upload, and author subscription flows. Direct material purchases, protected buyer downloads, seller payouts, and commission accounting are planned as optional v2 work.

## Why It Matters

Independent teachers often create useful learning materials but lack simple infrastructure to present them, moderate quality, and connect with buyers inside the communication channels they already use. Telegram is a natural entrypoint for many local teacher communities, but most marketplace tooling is either too generic, too expensive, or not self-hostable.

TeacherMarket aims to become reusable open-source infrastructure for those communities.

## Current Status

- Early beta-ready product core.
- FastAPI API, aiogram bot, React/Vite Telegram Mini App, PostgreSQL, Alembic.
- Local/self-host setup documented.
- AGPL-3.0-only license selected.
- Community validation is in progress and must be documented before application.
- Public release gates are tracked in `docs/release-gates.md`.

## Maintainer Role

The maintainer is the creator and core maintainer of the project and related teacher ecosystem tools. The maintainer is responsible for product direction, security boundaries, release quality, community feedback, and open-source onboarding.

## Codex Use Cases

Codex can help with real maintainer workload:

- review pull requests for security and regression risks;
- triage beta feedback into scoped GitHub issues;
- write and maintain API, bot, and webapp tests;
- improve file-upload and payment-webhook security;
- validate Alembic migrations;
- update self-hosting and contributor docs;
- prepare release notes and release checklists;
- onboard first-time contributors with issue drafts and code pointers.

## Proof Points To Gather

| Proof point | Status | Notes |
|---|---|---|
| Teacher community size | TBD | Document honestly in `docs/community-validation.md`. |
| Poll results | TBD | Include anonymized counts/screenshots if safe. |
| Seller interest | TBD | Count teachers interested in publishing materials. |
| Buyer/user interest | TBD | Count teachers interested in finding materials. |
| Beta testers | TBD | Keep private contacts out of public docs. |
| First sample materials | TBD | Use demo or consented public materials only. |
| Public feedback issues | TBD | Link GitHub issues labeled `community-feedback`. |
| CI and tests | In progress | CI added; GitHub run still pending after push. |

## Suggested Application Text

```text
TeacherMarket is an open-source, self-hostable, Telegram-first catalog engine for teacher communities. It helps teachers publish educational materials, manage seller profiles, pass moderation, receive contact requests, and run a learning-materials catalog through a Telegram bot and Mini App.

The project is being developed around an existing teacher ecosystem and early beta validation. The OSS core is designed to be useful on its own for communities that want to self-host a catalog, while future hosted/cloud features can extend it without locking the core.

Codex would help me maintain the project by reviewing pull requests, triaging issues from beta users, improving security around file uploads and subscription payments, writing tests, maintaining migrations, improving documentation, and preparing releases.
```

## Wording To Avoid

Do not claim:

- broad adoption before public validation exists;
- production-scale usage before launch;
- direct material checkout in OSS v1;
- seller payouts in OSS v1;
- community numbers that are not documented.

Prefer:

- “being developed around an existing teacher community”;
- “early MVP”;
- “beta validation in progress”;
- “self-hostable open-source core”;
- “first teacher testers.”
