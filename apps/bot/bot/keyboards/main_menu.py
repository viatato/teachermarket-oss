from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def is_https_url(url: str) -> bool:
    return url.strip().lower().startswith("https://")


def open_market_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    if not is_https_url(webapp_url):
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❓ Як відкрити Mini App", callback_data="help")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="main:menu")],
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 Відкрити маркет",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="main:menu")],
        ]
    )


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="main:menu")],
        ]
    )


def main_menu(webapp_url: str, *, is_admin: bool = False) -> InlineKeyboardMarkup:
    keyboard = []
    if is_https_url(webapp_url):
        keyboard.append(
            [
            InlineKeyboardButton(
                text="🛍 Відкрити маркет",
                web_app=WebAppInfo(url=webapp_url),
            )
            ]
        )

    keyboard.extend(
        [
        [
            InlineKeyboardButton(text="🔎 Знайти матеріали", callback_data="buyer:search"),
            InlineKeyboardButton(text="⭐ Збережене", callback_data="buyer:favorites"),
        ],
        [
            InlineKeyboardButton(text="➕ Додати матеріал", callback_data="seller:add_product"),
            InlineKeyboardButton(text="👤 Кабінет автора", callback_data="seller:dashboard"),
        ],
        [InlineKeyboardButton(text="❓ Допомога", callback_data="help")],
        ]
    )
    if is_admin:
        keyboard.append([InlineKeyboardButton(text="🛡 Адмін-панель", callback_data="admin:dashboard")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
