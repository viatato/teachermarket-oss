import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.api_client import ApiClient
from bot.config import get_settings
from bot.keyboards.main_menu import is_https_url, main_menu


router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start(message: Message) -> None:
    settings = get_settings()
    if message.from_user:
        try:
            await ApiClient().upsert_bot_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                language_code=message.from_user.language_code,
            )
        except Exception:
            logger.exception("Failed to upsert Telegram user from /start")

    text = (
        "👋 Вітаємо в ТічерМаркеті!\n\n"
        "Тут викладачі знаходять готові матеріали для уроків і напряму звʼязуються з авторами."
    )
    if not is_https_url(settings.webapp_url):
        text += (
            "\n\n"
            "Mini App зараз налаштований на локальний URL. Telegram відкриває Web App тільки через HTTPS, "
            "тому для кнопки маркету потрібен tunnel або production URL."
        )

    await message.answer(
        text,
        reply_markup=main_menu(
            settings.webapp_url,
            is_admin=bool(message.from_user and message.from_user.id in settings.admin_ids),
        ),
    )
