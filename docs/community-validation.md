# Community Validation

This document tracks public-safe demand signals for TeacherMarket from the teacher community. It is intended to support the public OSS launch and the OpenAI Codex for Open Source application without exposing private teacher identities, Telegram handles, phone numbers, paid materials, screenshots with personal data, or private support notes.

## Current Status

Community validation is in progress and the hosted beta has started. The maintainer already has:

- a TeacherMarket product-interest poll with 11 responses;
- a broader teacher problems-and-pain-points poll with 33 responses;
- a Telegram teacher community with 1,461 members;
- 8 testers for the hosted TeacherMarket Cloud beta.

Keep raw response exports, optional Telegram usernames, emails, and private support notes outside the public repository.

## Source Forms

| Form | Purpose | Public-safe source | Response data |
|---|---|---|---|
| `Кастдев Тічери` | Broader teacher customer-development poll about format, routine, pain points, AI/tool usage, and testing interest. | https://docs.google.com/forms/d/1pzzWlA5pK7ugxnsMrxQbT2JQtz9awcekWcsLrnan1vk/viewform | Keep response export private; summarize only aggregate counts and themes. |
| `ТічерМаркет — опитування для викладачів` | TeacherMarket-specific validation poll for catalog usefulness, author/user interest, feature priorities, contact-author flow, beta testing, and material categories. | https://docs.google.com/forms/d/1zh3SD0lbMiFxQQTL4-WQCOy6FV9KlMZ1BHVINnsmgik/viewform | Keep response export private; summarize only aggregate counts and themes. |

## Demand Signals

| Signal | Public-safe value | Evidence to keep/link |
|---|---:|---|
| Teacher community size | 1,461 members | Public-safe Telegram community screenshot |
| TeacherMarket poll respondents | 11 | Google Forms responses summary screenshot |
| Customer-development poll respondents | 33 | Google Forms responses summary screenshot |
| Potential authors/sellers | 5 interested in publishing materials; 6 want beta as authors | TeacherMarket poll questions 2 and 6 |
| Potential users/buyers | 3 interested in finding materials; 2 want beta as catalog users | TeacherMarket poll questions 2 and 6 |
| Interested beta testers | 8 direct yes responses; 10 including "maybe later" | TeacherMarket poll question 6 |
| Cloud beta testers already onboarded | 8 | Private tester list kept outside repo |
| Public feedback issues | 4 feedback issues created | GitHub issues #4, #5, #6, and #7 |

## TeacherMarket Product-Interest Poll

Use this section to summarize `ТічерМаркет — опитування для викладачів` after removing private details.

Key questions:

- respondent role: language teacher, other subject teacher, education worker, or interested non-teacher;
- usefulness of a Telegram-first catalog for learning materials;
- most important catalog features;
- material categories respondents want to publish or find;
- comfort with the contact-author-in-Telegram flow;
- beta test interest;
- missing features;
- optional Telegram username or email for beta invitation.

Public-safe result summary:

- Respondents: 11.
- Respondent profile: 9 language teachers, 1 education worker who does not teach directly, and 1 interested non-teacher.
- Catalog usefulness: 5 would publish materials, 3 would search for lesson materials, 1 is interested as a beta tester, 2 need more context, and 0 said it is not currently relevant.
- Beta interest: 6 want to test as authors, 2 want to test as catalog users, 2 might join later, and 1 said no.
- Contact-author flow: 8 of 11 are comfortable with the direct Telegram contact model, 1 would prefer in-platform purchasing, 2 are unsure, and 0 said the model does not fit.

Most important catalog features:

- Convenient material upload: 8 of 11.
- Catalog, search, and filters: 6 of 11.
- Material previews before contacting the author: 6 of 11.
- Simple Telegram format: 5 of 11.
- Favorites: 5 of 11.
- Quality moderation, direct author contact, and clear author rules: 3 of 11 each.

Most requested material categories:

- Lesson plans: 7 of 11.
- Worksheets and lexical materials: 6 of 11 each.
- Speaking cards and Miro materials: 5 of 11 each.
- Presentations, grammar materials, and adult materials: 4 of 11 each.
- Tests/quizzes and children's materials: 3 of 11 each.

## Problems And Pain Points Poll

Use this section to summarize `Кастдев Тічери`.

Key questions:

- current work format: private tutor, small team, online school/course owner, or education project producer;
- current active student/client count;
- where teachers find new students;
- top routine/time drains outside lessons;
- biggest annoyance or energy drain;
- one task teachers would delegate to a tool;
- current AI usage;
- paid work tools used in the last 6 months;
- testing interest for a new teacher product.

Record 3-5 strongest themes from the teacher audience:

- Teacher audience composition: 21 of 33 respondents are private tutors, 5 have a small team, and 7 own online schools or courses.
- Audience scale: 14 of 33 have 5-15 active students, 13 have 15-50, 3 have up to 5, and 3 have 50+.
- New student acquisition is mostly informal and Telegram/social-channel based: recommendations are used by 32 of 33, Telegram channels or broadcasts by 20, Instagram by 15, tutor platforms by 8, targeted ads by 6, and TikTok by 4.
- Biggest time drains outside lessons are homework checking or lesson-material preparation (24 of 33), finding new students or sales (22), potential-client messaging (15), content creation (13), and technical setup such as sites, payments, and Zoom (9).
- Open-ended answers repeatedly mention payment reminders/checking, finding students, social media, client communication, homework/material preparation, and routine admin as high-energy drains.
- AI readiness is high: 26 of 33 use AI almost daily and 7 use it sometimes.

## Roadmap Conclusions

Translate validated feedback into a small public roadmap:

- Prioritize catalog search, filters, and clear material cards for the first public beta.
- Keep the contact-author flow explicit because OSS v1 does not process direct purchases or payouts.
- Improve author onboarding, upload guidance, and material description templates.
- Keep moderation, reports, and quality rules visible for self-hosted communities.
- Treat payment, rating, and stronger preview/navigation requests as validated future backlog while keeping direct material checkout out of OSS v1.
- Convert repeated feedback into GitHub issues labeled `community-feedback`.

## Feedback-Derived Issue Candidates

These public GitHub issues were created from beta/community feedback. Keep them scoped and label them `community-feedback`.

| Feedback item | Suggested public issue title | Suggested labels |
|---|---|---|
| Automoderation | [#6 Add optional automoderation assist for submitted materials](https://github.com/viatato/teachermarket-oss/issues/6) | `community-feedback`, `moderation`, `security`, `codex-friendly` |
| One-time upload/payment request | [#5 Explore one-time author upload fee option for self-hosters](https://github.com/viatato/teachermarket-oss/issues/5) | `community-feedback`, `payments`, `self-hosting`, `help wanted` |
| Tariff changes | [#4 Allow authors to change subscription plans safely](https://github.com/viatato/teachermarket-oss/issues/4) | `community-feedback`, `payments`, `backend`, `frontend` |
| Complaints about materials | [#7 Improve material complaint/report handling and policy docs](https://github.com/viatato/teachermarket-oss/issues/7) | `community-feedback`, `moderation`, `frontend`, `documentation` |

## Public Evidence Rules

- Use aggregate counts instead of private respondent lists.
- Redact names, phone numbers, Telegram handles, school names, and private material titles unless explicit consent exists.
- Store raw poll exports and beta tester contacts outside this repository.
- Use consented short quotes only when they do not reveal private identity or copyrighted material.
- Link public GitHub issues for product feedback instead of copying private support threads.
