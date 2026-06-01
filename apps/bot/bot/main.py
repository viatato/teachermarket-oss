import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import get_settings
from bot.routers.admin_moderation import router as admin_moderation_router
from bot.routers.menu import router as menu_router
from bot.routers.product_creation import router as product_creation_router
from bot.routers.seller import router as seller_router
from bot.routers.start import router as start_router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()

    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(start_router)
    dispatcher.include_router(admin_moderation_router)
    dispatcher.include_router(product_creation_router)
    dispatcher.include_router(seller_router)
    dispatcher.include_router(menu_router)

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
