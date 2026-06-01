# Demo Flow

Use this script for screenshots, demos, and public README assets after the UI is verified.

## Seed Demo

```bash
docker compose up -d postgres
cd apps/api
alembic upgrade head
python -m app.db.seed
```

Demo seed data includes:

- Free, monthly Pro, and yearly Pro subscription plans.
- One demo seller profile.
- Several published example materials with generated preview fallback assets.

## Screenshot Checklist

- [ ] Catalog with filters and product cards.
- [ ] Product detail page with preview carousel and contact-author CTA.
- [ ] Favorites screen.
- [ ] Seller dashboard overview.
- [ ] Seller product management.
- [ ] Seller subscription screen.
- [ ] Admin moderation panel.
- [ ] Report/review UI.

Do not include real Telegram IDs, private teacher contacts, private files, secrets, or production payment details in screenshots.

## Demo Narrative

1. A buyer opens the Telegram Mini App from the bot.
2. The buyer browses catalog materials and filters by audience, level, category, or price.
3. The buyer opens a material, reviews previews, saves it, and contacts the author.
4. A teacher creates an author profile, uploads a material, and submits it for moderation.
5. An admin approves or rejects the material.
6. The author manages subscription limits and sees contact requests.

TeacherMarket OSS v1 stops at contact-author and author-subscription flows. It does not process payment for a specific material.
