# TeacherMarket Open Source Implementation Plan

> Archived original plan. This document is kept for traceability only and is superseded by `docs/implementation-plan.md`.
> Some MVP sections below describe direct material orders/download access; those are not OSS v1 scope and are now v2 design work.

> This document is the main implementation plan for Codex and contributors.
> Goal: build TeacherMarket as an open-source, self-hostable marketplace engine for teachers and education communities, while keeping a commercial hosted version possible.

---

## 1. Project Vision

TeacherMarket is an open-source Telegram-first marketplace engine for independent teachers, tutors, methodologists, and small education communities.

The project should allow teacher communities to:

- publish and sell digital learning materials;
- create seller profiles;
- manage educational products;
- process orders;
- deliver digital files after purchase;
- moderate content;
- run the marketplace inside Telegram through a bot and Telegram Mini App;
- optionally self-host their own marketplace.

TeacherMarket is part of a broader teacher ecosystem:

- **Тічер Тусовка** — existing teacher community and adoption channel;
- **TeacherMarket Core** — open-source marketplace engine;
- **TeacherMarket Cloud** — commercial hosted version;
- **TeacherBoard** — separate CRM/productivity tool for teachers, not necessarily fully open-source.

The open-source version must be useful on its own, not just a demo or crippled version.

---

## 2. Strategic Goal

The project should be prepared for two goals at the same time:

1. **Real product goal**
   - Build a useful marketplace for teachers and education creators.
   - Use the existing teacher community as the first adoption channel.
   - Allow real beta testing and future monetization.

2. **OpenAI Codex for Open Source application goal**
   - Present TeacherMarket as a real open-source infrastructure project.
   - Show active maintenance potential.
   - Show community demand.
   - Show clear maintainer workload where Codex can help:
     - code review;
     - security hardening;
     - issue triage;
     - tests;
     - documentation;
     - contributor onboarding;
     - release automation.

---

## 3. Product Positioning

### Short positioning

TeacherMarket is an open-source marketplace engine for teachers and education communities.

### Longer positioning

TeacherMarket is a self-hostable, Telegram-first marketplace engine that helps independent teachers and small education communities sell, distribute, and manage digital learning materials. It includes seller profiles, product catalogs, digital file delivery, basic moderation, order management, and payment/storage adapters.

### What it is not

TeacherMarket is not just one closed marketplace owned by one person.

TeacherMarket Core should be a reusable engine that other teacher communities can adapt and run.

---

## 4. Open-Core Model

TeacherMarket should use an **open-core** model.

### Open-source part

Repository: `teachermarket-core`

Includes:

- Telegram Mini App frontend;
- Telegram bot;
- backend API;
- database schema and migrations;
- marketplace business logic;
- seller profiles;
- product catalog;
- digital file delivery;
- basic order management;
- basic moderation;
- plugin interfaces;
- payment provider interfaces;
- storage provider interfaces;
- local development setup;
- Docker setup;
- documentation;
- contributor guide;
- security policy.

### Commercial/private part

Repository: `teachermarket-cloud`

Includes:

- hosted infrastructure;
- managed deployments;
- seller payouts;
- commission engine;
- advanced analytics;
- paid promotion tools;
- internal moderation dashboard;
- AI tools for product descriptions;
- premium seller profiles;
- recommendation system;
- marketplace ranking;
- fraud/risk scoring;
- private operational tooling;
- support/admin features.

The commercial version should import and extend the open-source core instead of duplicating the whole app.

---

## 5. Recommended Repository Structure

```txt
teachermarket-core/
  apps/
    web/                  # Telegram Mini App / web frontend
    bot/                  # Telegram bot
    api/                  # Backend API

  packages/
    core/                 # Shared business logic
    db/                   # Database schema, migrations, seed data
    ui/                   # Shared UI components
    auth/                 # Auth/session helpers
    payments/             # Payment provider interfaces + basic adapters
    storage/              # Storage provider interfaces + local/S3-compatible adapter
    notifications/        # Telegram/email notification abstractions
    config/               # Shared config and env validation

  plugins/
    payments-manual/      # Manual payment confirmation for MVP
    payments-wayforpay/   # Optional public adapter if safe
    storage-local/        # Local storage for self-host
    storage-s3/           # S3-compatible storage adapter

  docs/
    architecture.md
    self-hosting.md
    contributing.md
    security.md
    roadmap.md
    codex.md
    openai-application-notes.md

  .github/
    ISSUE_TEMPLATE/
    workflows/
      ci.yml
      lint.yml
      test.yml

  docker-compose.yml
  README.md
  LICENSE
  AGENTS.md
  CONTRIBUTING.md
  SECURITY.md
  CODE_OF_CONDUCT.md
  CHANGELOG.md
```

---

## 6. Suggested Tech Stack

The exact stack can change, but the project should stay simple and contributor-friendly.

### Frontend

Recommended:

- Next.js or Vite + React;
- TypeScript;
- Tailwind CSS;
- Telegram Mini App SDK;
- basic component system.

### Backend

Recommended:

- Node.js;
- TypeScript;
- Fastify / Hono / NestJS;
- REST API first;
- optional tRPC later only if it does not complicate OSS adoption.

### Database

Recommended:

- PostgreSQL;
- Prisma or Drizzle;
- clear migrations;
- seed data for local demo.

### Bot

Recommended:

- Telegraf or grammY;
- Telegram webhook support;
- local polling mode for development.

### Storage

MVP:

- local storage adapter.

Production-ready:

- S3-compatible storage adapter;
- R2 compatibility later.

### Payments

MVP:

- manual payment confirmation;
- fake/test payment provider;
- payment provider interface.

Later:

- WayForPay;
- Stripe;
- Monobank;
- Fondy or other local providers if useful.

### Infrastructure

- Docker Compose for local setup;
- GitHub Actions for CI;
- `.env.example`;
- deployment docs for VPS;
- optional Railway/Fly.io/Render guide later.

---

## 7. Core Domain Model

Initial entities:

### User

Represents a Telegram user or web user.

Fields:

- id;
- telegram_id;
- username;
- first_name;
- last_name;
- role;
- created_at;
- updated_at.

Roles:

- buyer;
- seller;
- moderator;
- admin.

### SellerProfile

Represents a teacher/creator profile.

Fields:

- id;
- user_id;
- display_name;
- bio;
- avatar_url;
- subjects;
- languages;
- country;
- social_links;
- status;
- created_at;
- updated_at.

Statuses:

- draft;
- pending_review;
- approved;
- suspended.

### Product

Represents a digital material.

Fields:

- id;
- seller_id;
- title;
- slug;
- description;
- short_description;
- subject;
- language;
- level;
- format;
- price;
- currency;
- preview_images;
- preview_file_url;
- main_file_id;
- status;
- moderation_status;
- created_at;
- updated_at.

Statuses:

- draft;
- published;
- hidden;
- archived.

Moderation statuses:

- not_submitted;
- pending;
- approved;
- rejected.

### ProductFile

Represents uploaded files.

Fields:

- id;
- product_id;
- storage_provider;
- storage_key;
- filename;
- mime_type;
- size;
- checksum;
- created_at.

### Order

Represents a purchase.

Fields:

- id;
- buyer_id;
- seller_id;
- product_id;
- amount;
- currency;
- status;
- payment_provider;
- payment_reference;
- created_at;
- paid_at;
- completed_at.

Statuses:

- pending;
- paid;
- completed;
- refunded;
- cancelled;
- failed.

### DownloadAccess

Represents access to a purchased file.

Fields:

- id;
- order_id;
- buyer_id;
- product_id;
- expires_at;
- download_limit;
- download_count;
- created_at.

### Review

Represents product/seller feedback.

Fields:

- id;
- product_id;
- buyer_id;
- rating;
- text;
- status;
- created_at.

### ModerationEvent

Tracks moderation actions.

Fields:

- id;
- moderator_id;
- entity_type;
- entity_id;
- action;
- reason;
- created_at.

---

## 8. MVP Scope

The MVP should prove that TeacherMarket can work as a real teacher marketplace.

### MVP must include

- Telegram login or Telegram user identity flow;
- seller profile creation;
- product creation;
- product catalog;
- product detail page;
- basic search/filter;
- file upload;
- manual payment flow;
- order creation;
- admin/manual order approval;
- file delivery after approved payment;
- basic moderation;
- basic admin dashboard;
- Docker local setup;
- seed demo data;
- README with screenshots;
- contribution guide;
- security policy.

### MVP can skip

- automatic payouts;
- advanced analytics;
- promotion tools;
- AI tools;
- complex recommendations;
- affiliate system;
- multi-tenant white-label mode;
- enterprise moderation;
- automatic tax logic.

---

## 9. MVP User Flows

### Buyer flow

1. User opens Telegram bot.
2. Bot sends link to Telegram Mini App.
3. User browses product catalog.
4. User opens product page.
5. User clicks buy.
6. Order is created.
7. User receives payment instructions or test checkout.
8. Admin/seller confirms payment.
9. User receives download access.
10. User downloads the material.

### Seller flow

1. Teacher opens seller registration page.
2. Teacher creates seller profile.
3. Teacher creates product.
4. Teacher uploads preview and main file.
5. Product goes to moderation.
6. Moderator approves product.
7. Product appears in catalog.
8. Seller can see orders.

### Admin/moderator flow

1. Admin opens dashboard.
2. Admin sees pending seller profiles.
3. Admin approves/rejects seller profile.
4. Admin sees pending products.
5. Admin approves/rejects products.
6. Admin sees pending orders.
7. Admin confirms manual payment.
8. Buyer receives file access.

---

## 10. Plugin/Adapter Architecture

TeacherMarket Core should use interfaces for replaceable parts.

### Payment provider interface

```ts
export interface PaymentProvider {
  id: string

  createCheckout(input: CreateCheckoutInput): Promise<CheckoutSession>

  verifyWebhook(input: VerifyWebhookInput): Promise<PaymentWebhookResult>

  refund?(input: RefundInput): Promise<RefundResult>
}
```

MVP providers:

- manual payment provider;
- fake test provider.

Later providers:

- WayForPay;
- Stripe;
- Monobank;
- other local providers.

### Storage provider interface

```ts
export interface StorageProvider {
  id: string

  upload(input: UploadInput): Promise<StoredFile>

  getSignedDownloadUrl(input: DownloadInput): Promise<string>

  delete(input: DeleteInput): Promise<void>
}
```

MVP providers:

- local storage.

Later providers:

- S3;
- Cloudflare R2;
- MinIO.

### Notification provider interface

```ts
export interface NotificationProvider {
  sendTelegramMessage(input: TelegramMessageInput): Promise<void>
  sendEmail?(input: EmailInput): Promise<void>
}
```

MVP:

- Telegram notifications only.

---

## 11. Security Requirements

Security is important because the project handles:

- teacher accounts;
- buyer accounts;
- digital files;
- payments;
- seller data;
- download links.

### Required before public launch

- validate all environment variables;
- never commit secrets;
- add `.env.example`;
- add basic rate limiting;
- validate uploaded file types;
- limit file size;
- scan or at least restrict risky uploads;
- prevent public direct access to paid files;
- use signed download links;
- verify payment webhooks;
- protect admin routes;
- use role-based access control;
- avoid exposing internal order/payment data to buyers;
- log moderation actions;
- add security disclosure process in `SECURITY.md`.

### Security issues for Codex

Create GitHub issues:

- harden file upload validation;
- add signed download URL expiration;
- add payment webhook verification;
- add RBAC tests;
- add rate limiting;
- add audit log for admin actions;
- add dependency scanning;
- add Docker security checklist.

---

## 12. Documentation Requirements

The project must look serious and maintainable.

### Required docs

#### README.md

Must include:

- one-line pitch;
- screenshots;
- demo GIF/video link if possible;
- feature list;
- project status;
- quick start;
- architecture overview;
- tech stack;
- self-hosting summary;
- contribution link;
- license;
- community link;
- roadmap link.

#### AGENTS.md

Must include:

- project overview for Codex;
- commands to run;
- architecture map;
- coding conventions;
- testing instructions;
- PR expectations;
- security notes;
- files/folders Codex should not modify without care.

#### CONTRIBUTING.md

Must include:

- how to set up locally;
- how to pick an issue;
- branch naming;
- commit style;
- PR checklist;
- code style;
- testing rules.

#### SECURITY.md

Must include:

- supported versions;
- how to report vulnerabilities;
- what counts as sensitive;
- security expectations for payments/files/auth.

#### ROADMAP.md

Must include:

- MVP;
- beta;
- public release;
- post-MVP;
- commercial/hosted separation.

#### SELF_HOSTING.md

Must include:

- requirements;
- Docker setup;
- env variables;
- database setup;
- Telegram bot setup;
- storage setup;
- payment setup;
- deployment notes.

---

## 13. GitHub Issue Structure

Create labels:

- `good first issue`;
- `help wanted`;
- `documentation`;
- `security`;
- `backend`;
- `frontend`;
- `bot`;
- `payments`;
- `storage`;
- `moderation`;
- `mvp`;
- `codex-friendly`;
- `community-feedback`.

Create milestones:

1. `MVP Foundation`
2. `Teacher Community Beta`
3. `Security Hardening`
4. `Open Source Launch`
5. `Codex for OSS Application`

### Initial issues

#### Foundation

- Set up monorepo structure.
- Add TypeScript config.
- Add database schema.
- Add Docker Compose.
- Add env validation.
- Add seed data.
- Add CI workflow.

#### Marketplace

- Implement seller profile model.
- Implement product model.
- Implement product catalog page.
- Implement product detail page.
- Implement order creation.
- Implement manual payment flow.
- Implement download access.

#### Bot/TWA

- Set up Telegram bot.
- Add bot start command.
- Add Mini App launch button.
- Connect Telegram user identity.
- Add buyer notifications.
- Add seller notifications.

#### Moderation

- Add seller approval flow.
- Add product moderation flow.
- Add moderation event log.
- Add admin dashboard.

#### Security

- Add RBAC.
- Add file upload validation.
- Add signed download links.
- Add rate limiting.
- Add audit logging.
- Add dependency scanning.

#### Documentation

- Write README.
- Write AGENTS.md.
- Write CONTRIBUTING.md.
- Write SECURITY.md.
- Write SELF_HOSTING.md.
- Write ROADMAP.md.

#### Community

- Add community feedback discussion.
- Add beta tester waitlist.
- Add teacher use cases.
- Add sample marketplace data.

---

## 14. Implementation Phases

## Phase 0 — Product/OSS Preparation

Goal: define the product clearly before coding too much.

Tasks:

- define exact MVP scope;
- choose license;
- choose stack;
- create public repository;
- write initial README;
- write roadmap;
- add AGENTS.md;
- add issue templates;
- create GitHub labels and milestones;
- create community feedback form;
- run a poll in the teacher community;
- collect beta tester interest.

Deliverables:

- public repo exists;
- README explains vision;
- roadmap exists;
- teacher community demand is documented;
- first GitHub issues are created.

---

## Phase 1 — Technical Foundation

Goal: make the project easy to run locally.

Tasks:

- set up monorepo;
- set up TypeScript;
- set up frontend app;
- set up backend app;
- set up bot app;
- set up PostgreSQL;
- set up ORM;
- create base schema;
- add Docker Compose;
- add `.env.example`;
- add env validation;
- add linting;
- add formatting;
- add CI;
- add seed data.

Deliverables:

- `docker-compose up` works;
- backend starts;
- frontend starts;
- bot starts in dev mode;
- database migrations work;
- CI passes.

---

## Phase 2 — Core Marketplace MVP

Goal: implement core marketplace features.

Tasks:

- implement user model;
- implement seller profile;
- implement product model;
- implement product creation;
- implement file upload;
- implement catalog page;
- implement product page;
- implement order creation;
- implement manual payment provider;
- implement payment confirmation;
- implement download access;
- implement buyer download page.

Deliverables:

- seller can create product;
- buyer can create order;
- admin can confirm payment;
- buyer can download purchased file.

---

## Phase 3 — Telegram Integration

Goal: make the marketplace Telegram-first.

Tasks:

- implement Telegram bot `/start`;
- connect Telegram identity to user;
- add Mini App launch button;
- send order notifications;
- send payment instructions;
- send download confirmation;
- notify seller about new order;
- notify moderator about pending products.

Deliverables:

- user can start from Telegram;
- bot routes user into Mini App;
- important events trigger Telegram notifications.

---

## Phase 4 — Moderation and Admin

Goal: make the marketplace safe enough for beta.

Tasks:

- implement admin role;
- implement moderator role;
- implement seller approval;
- implement product moderation;
- implement product rejection reason;
- implement moderation log;
- add admin dashboard;
- add order management screen.

Deliverables:

- admin can approve sellers;
- moderator can approve products;
- moderation actions are logged;
- marketplace is not fully open to spam.

---

## Phase 5 — Security Hardening

Goal: prepare for real beta users and open-source credibility.

Tasks:

- add RBAC tests;
- add protected admin routes;
- add upload size limits;
- add upload MIME validation;
- add signed download URLs;
- add download limits;
- add rate limiting;
- add webhook verification abstraction;
- add audit logging;
- add dependency scanning;
- add security docs.

Deliverables:

- core security checklist is complete;
- security issues are documented;
- project is safe enough for limited beta.

---

## Phase 6 — OSS Launch

Goal: make the repo look serious and contributor-ready.

Tasks:

- finalize README;
- add screenshots;
- add local demo data;
- add demo video/GIF;
- finish CONTRIBUTING;
- finish SECURITY;
- finish SELF_HOSTING;
- finish ROADMAP;
- add issue templates;
- mark good first issues;
- add project board;
- create first release;
- write launch post for teacher community;
- invite beta testers.

Deliverables:

- public release exists;
- contributors can understand the project;
- teachers can understand the product;
- Codex has enough context to work effectively.

---

## Phase 7 — Teacher Community Beta

Goal: prove demand from the existing teacher community.

Tasks:

- run poll in teacher chat;
- collect beta testers;
- collect seller candidates;
- collect sample materials;
- invite first sellers;
- test product publishing;
- test purchase/download flow;
- collect feedback;
- convert feedback into GitHub issues;
- document community demand.

Deliverables:

- beta tester list;
- seller interest list;
- real feedback issues;
- first real product examples;
- screenshots/testimonials if allowed.

---

## Phase 8 — OpenAI Codex for Open Source Application

Goal: prepare a strong application.

Tasks:

- make sure repository is public;
- ensure license is present;
- ensure README is strong;
- ensure maintainer role is clear;
- ensure issues and roadmap are visible;
- ensure community demand is documented;
- prepare short application description;
- prepare maintainer workload explanation;
- explain how Codex will help.

Deliverables:

- application-ready repo;
- application text;
- public proof of community demand;
- clear Codex use cases.

---

## 15. OpenAI Application Positioning

### Main narrative

TeacherMarket is an open-source marketplace engine for teachers and education communities. It is built around an existing teacher ecosystem, including a 1,500-member teacher community, and aims to help teachers sell and distribute educational materials through Telegram-first workflows.

### Why it matters

Independent teachers often create useful educational materials but do not have simple infrastructure to distribute, sell, and manage them. Existing platforms are either too general, too expensive, not Telegram-native, or not adaptable for local teacher communities.

TeacherMarket provides a self-hostable open-source alternative.

### Why Codex is useful

Codex would help the maintainer:

- review pull requests;
- triage issues from teacher beta users;
- improve file/payment security;
- write tests;
- improve documentation;
- generate migration scripts;
- onboard contributors;
- maintain release quality;
- reduce maintainer workload.

### Important proof points to gather

- teacher community size: 1,500 members;
- poll results;
- beta tester count;
- seller interest count;
- first product examples;
- GitHub stars/forks;
- open issues;
- contributor interest;
- public roadmap;
- screenshots/demo;
- self-hosting docs.

---

## 16. Suggested Application Text

Use this as a base, not necessarily final copy.

```txt
TeacherMarket is an open-source, Telegram-first marketplace engine for independent teachers and education communities. It helps teachers publish, sell, and distribute digital learning materials through seller profiles, product catalogs, order management, moderation, file delivery, and payment/storage adapters.

The project is part of a broader teacher ecosystem I maintain, including a 1,500-member teacher community and related teacher tools. The open-source core is designed to be self-hostable, so other teacher communities can adapt and run their own marketplaces instead of relying only on closed platforms.

Codex would help me maintain and grow the project by reviewing pull requests, triaging issues from beta users, improving security around payments and digital file delivery, writing tests, improving documentation, and helping onboard contributors.
```

---

## 17. Community Validation Plan

Before applying, collect visible signals.

### Poll questions for teacher chat

Question 1:

```txt
Вам був би корисний маркетплейс, де викладачі можуть продавати/купувати готові навчальні матеріали, шаблони, уроки, тести й презентації?
```

Options:

- Так, я б продавав/продавала свої матеріали.
- Так, я б купував/купувала матеріали.
- Мені цікаво як beta tester.
- Поки не актуально.

Question 2:

```txt
Що для вас найважливіше в такому маркетплейсі?
```

Options:

- Зручне завантаження матеріалів.
- Безпечна оплата.
- Каталог і пошук.
- Перевірка якості матеріалів.
- Можливість просувати свої матеріали.
- Простий Telegram-формат.

Question 3:

```txt
Які матеріали ви б хотіли продавати або купувати?
```

Open answers.

### Validation assets

Create:

- Google Form / Tally form;
- public GitHub discussion;
- issue called `Community feedback from teacher ecosystem`;
- short summary in `docs/community-validation.md`.

---

## 18. Commercial Separation Plan

TeacherMarket Core should stay self-hostable.

TeacherMarket Cloud should provide convenience and managed services.

### Core/free features

- self-hosting;
- seller profiles;
- product catalog;
- file upload;
- manual payments;
- basic moderation;
- order management;
- basic notifications;
- local/S3 storage adapters;
- docs.

### Cloud/paid features

- managed hosting;
- automatic updates;
- managed file storage;
- integrated payments;
- commission engine;
- seller payouts;
- advanced analytics;
- featured listings;
- promotion tools;
- AI descriptions;
- advanced moderation;
- support;
- branded marketplace for the existing community.

### Avoid

Do not make open-source core a fake shell.

Do not hide all useful features behind paid code.

Do not put private credentials, production configs, or private business logic in the public repo.

Do not make `if plan === "pro"` checks everywhere in the open-source core.

Prefer adapter interfaces and private cloud extensions.

---

## 19. License Recommendation

Recommended default: **AGPL-3.0**.

Reason:

- TeacherMarket is a SaaS-like marketplace engine.
- AGPL protects against someone taking the open-source code, hosting a competing service, and not sharing improvements.
- For a teacher/community marketplace, this tradeoff is acceptable.

Alternative:

- **Apache-2.0** if the priority is maximum adoption and minimum friction.
- **MIT** if the project should be extremely permissive.

Decision rule:

- choose AGPL-3.0 if protecting the hosted model matters most;
- choose Apache-2.0 if broad developer adoption matters most.

---

## 20. Codex Instructions

Codex should follow these rules when working on the project.

### General

- Keep the open-source core useful and self-hostable.
- Do not implement commercial-only features directly in the core unless they are generic extension points.
- Prefer simple, readable code over clever abstractions.
- Keep TypeScript strict.
- Add tests for business logic.
- Update docs when changing setup or architecture.
- Never commit secrets.
- Never hardcode production credentials.
- Keep payment and file access security in mind.

### Architecture

- Put shared business logic in `packages/core`.
- Put database schema and migrations in `packages/db`.
- Put frontend-only code in `apps/web`.
- Put bot-only code in `apps/bot`.
- Put API routes/controllers in `apps/api`.
- Use interfaces for payments, storage, and notifications.
- Keep private hosted features out of the public repository.

### Testing

Before marking a task complete:

- run lint;
- run typecheck;
- run tests;
- verify migrations;
- verify local seed data;
- update docs if needed.

### Pull request checklist

Every PR should answer:

- What changed?
- Why was it needed?
- How was it tested?
- Does it affect security?
- Does it affect self-hosting?
- Does it require documentation updates?

---

## 21. Definition of Done for Public OSS Launch

The project is ready for OSS launch when:

- repository is public;
- license is added;
- README is strong;
- local setup works;
- Docker setup works;
- seed data works;
- basic marketplace flow works;
- seller can create product;
- buyer can create order;
- admin can approve payment;
- buyer can download file;
- bot can open Mini App;
- moderation basics work;
- security docs exist;
- contributing docs exist;
- AGENTS.md exists;
- at least 10 starter issues exist;
- roadmap exists;
- first release is tagged.

---

## 22. Definition of Done for OpenAI Codex Application

The project is ready for application when:

- public repository exists;
- project has a clear OSS license;
- maintainer role is clear;
- README explains why the project matters;
- MVP or demo is visible;
- docs are good enough for contributors;
- issues and roadmap are active;
- community validation is documented;
- teacher community size is mentioned honestly;
- Codex use cases are specific;
- security and maintenance workload are clear.

---

## 23. Immediate Next Steps

1. Choose repository name.
2. Choose license.
3. Create public repo.
4. Add this plan as `docs/implementation-plan.md`.
5. Add `README.md`.
6. Add `AGENTS.md`.
7. Create GitHub labels and milestones.
8. Create first 20 issues.
9. Run teacher community poll.
10. Collect beta tester interest.
11. Build MVP foundation.
12. Add demo screenshots.
13. Prepare OpenAI application text.
14. Apply after repo has visible structure and community validation.

---

## 24. Suggested First Sprint

Duration: 7–10 days.

### Day 1

- Create repo.
- Add README.
- Add license.
- Add AGENTS.md.
- Add roadmap.
- Add issue templates.

### Day 2

- Set up monorepo.
- Set up TypeScript.
- Set up frontend/backend/bot apps.
- Add Docker Compose.
- Add PostgreSQL.

### Day 3

- Add database schema.
- Add user model.
- Add seller profile model.
- Add product model.

### Day 4

- Add product catalog.
- Add product page.
- Add seller product creation.

### Day 5

- Add file upload.
- Add manual payment flow.
- Add order model.

### Day 6

- Add admin order confirmation.
- Add download access.

### Day 7

- Add Telegram bot start flow.
- Add Mini App link.
- Add basic notifications.

### Day 8–10

- Add moderation.
- Add docs.
- Add screenshots.
- Create first release.
- Run community validation.

---

## 25. Notes for Maintainer

The strongest version of this project is not just a marketplace.

The strongest version is:

> open-source infrastructure for teacher communities.

The existing 1,500-member teacher chat is a major advantage, but it should be turned into visible validation:

- poll results;
- beta testers;
- seller interest;
- product examples;
- feedback issues;
- community discussion.

Do not rely only on the number.

Show that the community creates real maintainer workload and real product demand.

That is what makes the project more convincing for OpenAI Codex for Open Source.
