# OpenAI Codex For Open Source Application Notes

This document supports the current OpenAI Codex for Open Source application. Keep it honest: TeacherMarket is an early OSS core around an existing teacher ecosystem, not a widely adopted public platform yet.

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
| CI and tests | Active | GitHub Actions covers API tests, bot compile, and webapp build. |

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
TeacherMarket is a self-hostable Telegram-first catalog for teacher-created learning materials. It gives small teacher communities reusable infrastructure for author profiles, moderated listings, private files, reviews, reports, and buyer-author contact. Validation includes a 1,461-member teacher community, 44 aggregate poll responses, and 8 hosted beta testers. The active AGPL core has public CI, release gates, and maintained security boundaries.
```

### How will you use API credits?

```text
Use API credits for maintainer automation: PR and security review, issue triage, regression-test generation, migration checks, release-note drafting, and privacy-safe analysis of beta feedback. Credits would support the public AGPL core only; every generated change remains subject to maintainer review and CI before merge.
```

### Anything else we should know?

```text
I am the primary maintainer with write access. The public repository is intentionally separated from private production infrastructure and contains no customer data or deployment secrets. Current priorities are the first public beta, contributor onboarding, stronger payment and file tests, and optional human-in-the-loop moderation assistance.
```

## Application Readiness Actions

- Public aggregate validation, feedback issues, starter issues, release gates, CI, and security documentation are ready.
- The official form is `https://openai.com/form/codex-for-oss/`.
- The form was verified on June 14, 2026; the three narrative fields allow up to 500 characters.
- Submission still needs first name, last name, ChatGPT account email, OpenAI Organization ID, benefit selections, and personal acceptance of the program terms.
- Keep all personal account fields and the Organization ID out of this public repository.

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
