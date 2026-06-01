from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import get_settings
from bot.keyboards.main_menu import back_to_main_keyboard, is_https_url, main_menu, open_market_keyboard


router = Router()


@router.callback_query(F.data == "main:menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    settings = get_settings()
    await callback.message.answer(
        "Головне меню",
        reply_markup=main_menu(
            settings.webapp_url,
            is_admin=bool(callback.from_user and callback.from_user.id in settings.admin_ids),
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "buyer:search")
async def buyer_search(callback: CallbackQuery) -> None:
    settings = get_settings()
    if not is_https_url(settings.webapp_url):
        await callback.message.answer(
            "🔎 Каталог матеріалів відкривається у Mini App.\n\n"
            "Зараз `WEBAPP_URL` локальний. Telegram відкриває Web App тільки через HTTPS, "
            "тому для тесту потрібен tunnel або production URL.",
            reply_markup=back_to_main_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.answer(
        "🔎 Каталог матеріалів відкривається у Mini App.\n\n"
        "Там можна шукати матеріали, фільтрувати за мовою, рівнем і типом та писати авторам напряму.",
        reply_markup=open_market_keyboard(settings.webapp_url),
    )
    await callback.answer()


@router.callback_query(F.data == "buyer:favorites")
async def buyer_favorites(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "⭐ Розділ “Збережене” буде доступний у Mini App після підключення обраних матеріалів.",
        reply_markup=back_to_main_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_menu(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "❓ ТічерМаркет — це каталог матеріалів від викладачів.\n\n"
        "Покупці знаходять матеріал і пишуть автору напряму. Автори розміщують матеріали після модерації та можуть підключити підписку на сервіс.",
        reply_markup=back_to_main_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:dashboard")
async def admin_dashboard(callback: CallbackQuery) -> None:
    settings = get_settings()
    user_id = callback.from_user.id if callback.from_user else None
    if user_id not in settings.admin_ids:
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    await callback.message.answer(
        "🛡 Адмін-панель\n\n"
        "Тут можна модерувати матеріали й керувати підписками авторів.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Підписки авторів", callback_data="admin:subscriptions")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="main:menu")],
            ]
        ),
    )
    await callback.answer()
