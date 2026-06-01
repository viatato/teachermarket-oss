from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def moderation_keyboard(product_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👀 Подивитись файл", callback_data=f"admin:file:{product_id}"),
                InlineKeyboardButton(text="🖼 Превʼю", callback_data=f"admin:previews:{product_id}"),
            ],
            [
                InlineKeyboardButton(text="✅ Опублікувати", callback_data=f"admin:approve:{product_id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Відхилити", callback_data=f"admin:reject:{product_id}"),
                InlineKeyboardButton(text="✏️ Попросити правки", callback_data=f"admin:changes:{product_id}"),
            ],
            [
                InlineKeyboardButton(text="🙈 Сховати", callback_data=f"admin:hide:{product_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:dashboard"),
            ],
        ]
    )


def moderation_confirm_keyboard(action: str, product_id: str) -> InlineKeyboardMarkup:
    action_label = "опублікувати" if action == "approve" else "сховати"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Так, {action_label}",
                    callback_data=f"admin:{action}:confirm:{product_id}",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Назад до модерації", callback_data=f"admin:product:{product_id}")],
        ]
    )
