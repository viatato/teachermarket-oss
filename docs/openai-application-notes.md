# OpenAI Codex For Open Source Application Notes

This document is draft material for a future OpenAI Codex for Open Source application. Keep it honest: TeacherMarket is an early OSS core around an existing teacher ecosystem, not a widely adopted public platform yet.

## Short Project Description

TeacherMarket is an open-source, self-hostable, Telegram-first catalog engine for teacher communities. It helps teachers publish educational materials, manage seller profiles, pass moderation, receive contact requests from buyers, and run a catalog inside Telegram through a bot and Mini App.

OSS v1 focuses on catalog, contact-author, moderation, file upload, and author subscription flows. Direct material purchases, protected buyer downloads, seller payouts, and commission accounting are planned as optional v2 work.

## Why It Matters

Independent teachers often create useful learning materials but lack simple infrastructure to present them, moderate quality, and connect with buyers inside the communication channels they already use. Telegram is a natural entrypoint for many local teacher communities, but most marketplace tooling is either too generic, too expensive, or not self-hostable.

TeacherMarket aims to become reusable open-source infrastructure for those communities.

## Current Status

- Hosted beta has started.
- Early beta-ready product core.
- FastAPI API, aiogram bot, React/Vite Telegram Mini App, PostgreSQL, Alembic.
- Local/self-host setup documented.
- AGPL-3.0-only license selected.
- Existing Telegram teacher community has 1,461 members.
- TeacherMarket product-interest poll has 11 responses.
- Broader teacher problems-and-pain-points poll has 33 responses.
- Hosted TeacherMarket Cloud beta has 8 testers; keep their private contacts outside public docs.
- Community validation is summarized as public-safe aggregate counts in `docs/community-validation.md`.
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
| Teacher community size | 1,461 members | Public-safe Telegram community screenshot. |
| TeacherMarket product-interest poll results | 11 responses summarized | Use `ТічерМаркет — опитування для викладачів`; keep screenshots public-safe. |
| Problems/pain-points poll results | 33 responses summarized | Use `Кастдев Тічери`; summarize themes, not private respondent text. |
| Seller/author interest | 5 would publish; 6 want author beta | TeacherMarket poll questions 2 and 6. |
| Buyer/user interest | 3 would search; 2 want catalog-user beta | TeacherMarket poll questions 2 and 6. |
| Beta testers | 8 cloud beta testers | Keep private contacts out of public docs. |
| First sample materials | Optional before application | Use demo or consented public materials only. |
| Public feedback issues | 4 feedback issues created | #4 tariff changes, #5 one-time author upload fee option, #6 automoderation, #7 material complaint handling. |
| CI and tests | In progress | CI added; GitHub run still pending after push. |

## Suggested Application Text

```text
TeacherMarket is an open-source, self-hostable, Telegram-first catalog engine for teacher communities. It helps teachers publish educational materials, manage seller profiles, pass moderation, receive contact requests, and run a learning-materials catalog through a Telegram bot and Mini App.

The project is being developed around an existing teacher ecosystem and early beta validation. The OSS core is designed to be useful on its own for communities that want to self-host a catalog, while future hosted/cloud features can extend it without locking the core.

Codex would help me maintain the project by reviewing pull requests, triaging issues from beta users, improving security around file uploads and subscription payments, writing tests, maintaining migrations, improving documentation, and preparing releases.
```

## Form Field Drafts

Use these compact answers for the current OpenAI Codex for Open Source form.

### Why does this repository qualify?

```text
TeacherMarket is a self-hostable Telegram-first catalog engine for teacher communities. It addresses validated problems from an existing teacher audience: materials are shared through chats, folders, and DMs without catalog, moderation, author profiles, or reusable infrastructure. The OSS core is in early beta with real teacher testers and public maintainer work around docs, QA, security, and releases.
```

### How will you use API credits?

```text
I will use API credits for core OSS maintenance: PR review, issue triage from teacher beta feedback, test generation for FastAPI/bot/webapp flows, release checklist automation, documentation updates, and security review around Telegram auth, uploads, storage, moderation, and payment webhooks.
```

### Anything else we should know?

```text
TeacherMarket is intentionally scoped: OSS v1 focuses on catalog, author profiles, contact requests, moderation, file uploads, and subscriptions. Direct material checkout, protected downloads, seller payouts, and commission accounting are future v2 work, so the public repository stays honest and reusable for self-hosted education communities.
```

## Application Readiness Actions

- Fill `docs/community-validation.md` with aggregate counts from both polls and the cloud beta tester list.
- Use the `Кастдев Тічери` form for general teacher pain points and the `ТічерМаркет — опитування для викладачів` form for product-specific demand.
- Repeated beta feedback has been converted into public GitHub issues labeled `community-feedback`.
- Make sure `viatato/teachermarket-oss` and the maintainer GitHub profile are public before submitting.
- Confirm starter issues, release gates, CI status, and security docs are visible in the public repository.
- Prepare the OpenAI Organization ID before opening the form.

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
