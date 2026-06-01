import asyncio
from uuid import UUID

from sqlalchemy import text

from app.database import AsyncSessionLocal


ADMIN_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_SELLER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
DEMO_SELLER_ID = UUID("00000000-0000-0000-0000-000000000101")
FREE_PLAN_ID = UUID("00000000-0000-0000-0000-000000000201")
PRO_MONTHLY_PLAN_ID = UUID("00000000-0000-0000-0000-000000000202")
PRO_YEARLY_PLAN_ID = UUID("00000000-0000-0000-0000-000000000203")
DEMO_SUBSCRIPTION_ID = UUID("00000000-0000-0000-0000-000000000301")


PLANS = [
    {
        "id": FREE_PLAN_ID,
        "code": "free",
        "name": "Free",
        "description": "Безкоштовний старт для автора: до 3 опублікованих матеріалів.",
        "price_amount": 0,
        "currency": "UAH",
        "duration_days": 3650,
        "product_limit": 3,
    },
    {
        "id": PRO_MONTHLY_PLAN_ID,
        "code": "pro_monthly",
        "name": "Pro щомісяця",
        "description": "Більше матеріалів і готовність до майбутнього просування в каталозі.",
        "price_amount": 29900,
        "currency": "UAH",
        "duration_days": 30,
        "product_limit": 50,
    },
    {
        "id": PRO_YEARLY_PLAN_ID,
        "code": "pro_yearly",
        "name": "Pro на рік",
        "description": "Річний доступ для активних авторів.",
        "price_amount": 299000,
        "currency": "UAH",
        "duration_days": 365,
        "product_limit": 50,
    },
]


DEMO_PRODUCTS = [
    {
        "id": UUID("00000000-0000-0000-0000-000000001001"),
        "file_id": UUID("00000000-0000-0000-0000-000000002001"),
        "preview_id": UUID("00000000-0000-0000-0000-000000003001"),
        "preview_link_id": UUID("00000000-0000-0000-0000-000000004001"),
        "title": "30 Speaking Cards for A2 Teens",
        "description": "Картки для розмовної практики з підлітками на рівні A2.",
        "language": "english",
        "level": "a2",
        "category": "speaking_cards",
        "audience": "teens",
        "price_amount": 14900,
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000001002"),
        "file_id": UUID("00000000-0000-0000-0000-000000002002"),
        "preview_id": UUID("00000000-0000-0000-0000-000000003002"),
        "preview_link_id": UUID("00000000-0000-0000-0000-000000004002"),
        "title": "Present Perfect Test B1",
        "description": "Тест із граматики для перевірки Present Perfect на рівні B1.",
        "language": "english",
        "level": "b1",
        "category": "test",
        "audience": "teens",
        "price_amount": 9900,
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000001003"),
        "file_id": UUID("00000000-0000-0000-0000-000000002003"),
        "preview_id": UUID("00000000-0000-0000-0000-000000003003"),
        "preview_link_id": UUID("00000000-0000-0000-0000-000000004003"),
        "title": "Business English Meeting Phrases",
        "description": "Worksheet із корисними фразами для робочих зустрічей.",
        "language": "english",
        "level": "b2",
        "category": "worksheet",
        "audience": "business",
        "price_amount": 17900,
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000001004"),
        "file_id": UUID("00000000-0000-0000-0000-000000002004"),
        "preview_id": UUID("00000000-0000-0000-0000-000000003004"),
        "preview_link_id": UUID("00000000-0000-0000-0000-000000004004"),
        "title": "Kids Vocabulary Game: Animals",
        "description": "Гра для повторення лексики з дітьми на тему тварин.",
        "language": "english",
        "level": "kids",
        "category": "game",
        "audience": "kids",
        "price_amount": 12900,
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000001005"),
        "file_id": UUID("00000000-0000-0000-0000-000000002005"),
        "preview_id": UUID("00000000-0000-0000-0000-000000003005"),
        "preview_link_id": UUID("00000000-0000-0000-0000-000000004005"),
        "title": "Lesson Plan Template",
        "description": "Шаблон плану уроку для швидкої підготовки занять.",
        "language": "english",
        "level": "mixed",
        "category": "template",
        "audience": "teachers",
        "price_amount": 7900,
    },
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        for plan in PLANS:
            await session.execute(
                text(
                    """
                    INSERT INTO subscription_plans
                      (id, code, name, description, price_amount, currency, duration_days, product_limit, is_active)
                    VALUES
                      (:id, :code, :name, :description, :price_amount, :currency, :duration_days, :product_limit, true)
                    ON CONFLICT (code) DO UPDATE SET
                      name = EXCLUDED.name,
                      description = EXCLUDED.description,
                      price_amount = EXCLUDED.price_amount,
                      currency = EXCLUDED.currency,
                      duration_days = EXCLUDED.duration_days,
                      product_limit = EXCLUDED.product_limit,
                      is_active = true,
                      updated_at = now()
                    """
                ),
                plan,
            )

        await session.execute(
            text(
                """
                INSERT INTO users (id, telegram_id, username, first_name, language_code)
                VALUES
                  (:admin_id, 111111111, 'admin_placeholder', 'Адмін', 'uk'),
                  (:seller_user_id, 222222222, 'maria_teacher', 'Марія', 'uk')
                ON CONFLICT (telegram_id) DO NOTHING
                """
            ),
            {"admin_id": ADMIN_USER_ID, "seller_user_id": DEMO_SELLER_USER_ID},
        )

        await session.execute(
            text(
                """
                INSERT INTO seller_profiles
                  (id, user_id, display_name, bio, contact_username, contact_url, status)
                VALUES
                  (:seller_id, :user_id, 'Марія', 'Викладачка англійської, авторка матеріалів для підлітків і дорослих.', 'maria_teacher', 'https://t.me/maria_teacher', 'active')
                ON CONFLICT (user_id) DO UPDATE SET
                  display_name = EXCLUDED.display_name,
                  bio = EXCLUDED.bio,
                  contact_username = EXCLUDED.contact_username,
                  contact_url = EXCLUDED.contact_url,
                  status = EXCLUDED.status,
                  updated_at = now()
                """
            ),
            {"seller_id": DEMO_SELLER_ID, "user_id": DEMO_SELLER_USER_ID},
        )

        await session.execute(
            text(
                """
                INSERT INTO subscriptions (id, seller_id, plan_id, status, starts_at, expires_at)
                VALUES (:id, :seller_id, :plan_id, 'active', now(), now() + interval '3650 days')
                ON CONFLICT (id) DO UPDATE SET
                  seller_id = EXCLUDED.seller_id,
                  plan_id = EXCLUDED.plan_id,
                  status = EXCLUDED.status,
                  expires_at = EXCLUDED.expires_at,
                  updated_at = now()
                """
            ),
            {"id": DEMO_SUBSCRIPTION_ID, "seller_id": DEMO_SELLER_ID, "plan_id": FREE_PLAN_ID},
        )

        for product in DEMO_PRODUCTS:
            await session.execute(
                text(
                    """
                    INSERT INTO files
                      (id, owner_id, storage_key, original_filename, mime_type, file_size_bytes, file_kind)
                    VALUES
                      (:file_id, :owner_id, :product_storage_key, :product_filename, 'application/pdf', 102400, 'product_file'),
                      (:preview_id, :owner_id, :preview_storage_key, :preview_filename, 'image/png', 51200, 'preview_image')
                    ON CONFLICT (storage_key) DO NOTHING
                    """
                ),
                {
                    "file_id": product["file_id"],
                    "preview_id": product["preview_id"],
                    "owner_id": DEMO_SELLER_USER_ID,
                    "product_storage_key": f"demo/products/{product['id']}.pdf",
                    "preview_storage_key": f"demo/previews/{product['id']}.png",
                    "product_filename": f"{product['title']}.pdf",
                    "preview_filename": f"{product['title']} preview.png",
                },
            )
            await session.execute(
                text(
                    """
                    INSERT INTO products
                      (id, seller_id, title, description, language, level, category, audience, price_amount, currency, product_file_id, status, published_at)
                    VALUES
                      (:id, :seller_id, :title, :description, :language, :level, :category, :audience, :price_amount, 'UAH', :file_id, 'published', now())
                    ON CONFLICT (id) DO UPDATE SET
                      title = EXCLUDED.title,
                      description = EXCLUDED.description,
                      language = EXCLUDED.language,
                      level = EXCLUDED.level,
                      category = EXCLUDED.category,
                      audience = EXCLUDED.audience,
                      price_amount = EXCLUDED.price_amount,
                      status = EXCLUDED.status,
                      published_at = EXCLUDED.published_at,
                      updated_at = now()
                    """
                ),
                {**product, "seller_id": DEMO_SELLER_ID},
            )
            await session.execute(
                text(
                    """
                    INSERT INTO product_previews (id, product_id, file_id, sort_order)
                    VALUES (:preview_link_id, :id, :preview_id, 0)
                    ON CONFLICT (id) DO NOTHING
                    """
                ),
                product,
            )

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
