from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def seller_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Додати матеріал", callback_data="seller:add_product"),
                InlineKeyboardButton(text="📦 Мої матеріали", callback_data="seller:products"),
            ],
            [
                InlineKeyboardButton(text="📩 Звернення", callback_data="seller:requests"),
                InlineKeyboardButton(text="💳 Підписка", callback_data="seller:subscription"),
            ],
            [
                InlineKeyboardButton(text="📌 Правила сервісу", callback_data="seller:rules"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="main:menu"),
            ],
        ]
    )


def product_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Відправити на модерацію", callback_data="product:create_confirm"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="product:create_cancel"),
            ],
        ]
    )


def product_file_delivery_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔗 Додати посилання", callback_data="product:file_link"),
            ],
            [
                InlineKeyboardButton(text="💬 Передам у приватні повідомлення", callback_data="product:file_private"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="product:create_cancel"),
            ],
        ]
    )


def back_to_seller_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="seller:dashboard")],
        ]
    )


def cancel_to_seller_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="seller:profile_cancel")],
        ]
    )
