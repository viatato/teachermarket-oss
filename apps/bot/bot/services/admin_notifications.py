from aiogram import Bot
import logging

from bot.config import get_settings
from bot.keyboards.admin_moderation import moderation_keyboard


logger = logging.getLogger(__name__)


def moderation_message(product: dict[str, object]) -> str:
    price_amount = int(product.get("price_amount") or 0)
    price_uah = price_amount // 100
    return (
        "🆕 Новий матеріал на модерацію\n\n"
        f"Назва: {product.get('title')}\n"
        f"Ціна: {price_uah} грн\n"
        f"Мова: {product.get('language')}\n"
        f"Рівень: {product.get('level') or 'не вказано'}\n"
        f"Тип: {product.get('category')}\n"
        f"Аудиторія: {product.get('audience') or 'не вказано'}\n"
        f"Опис: {product.get('description') or 'не вказано'}"
    )


async def notify_admins_about_product(bot: Bot, product: dict[str, object]) -> None:
    settings = get_settings()
    product_id = str(product["id"])
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                moderation_message(product),
                reply_markup=moderation_keyboard(product_id),
            )
        except Exception:
            logger.exception("Failed to notify admin about product", extra={"admin_id": admin_id, "product_id": product_id})
