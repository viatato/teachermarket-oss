import logging

import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.api_client import ApiClient
from bot.config import get_settings
from bot.keyboards.admin_moderation import moderation_confirm_keyboard, moderation_keyboard
from bot.states.admin_moderation import AdminModerationStates


router = Router()
logger = logging.getLogger(__name__)


def product_id_from_callback(data: str) -> str:
    return data.rsplit(":", 1)[1]


def is_admin(user_id: int | None) -> bool:
    return bool(user_id and user_id in get_settings().admin_ids)


def subscription_line(item: dict[str, object]) -> str:
    seller = item.get("seller") if isinstance(item.get("seller"), dict) else {}
    plan = item.get("plan") if isinstance(item.get("plan"), dict) else {}
    seller_name = seller.get("display_name") or "Автор"
    username = seller.get("contact_username")
    plan_name = plan.get("name") if plan else None
    product_count = item.get("product_count")
    product_limit = item.get("product_limit")
    status_text = item.get("status") or "none"
    line = f"• {seller_name}"
    if username:
        line += f" (@{username})"
    line += f" — {plan_name or 'без активної підписки'}, {status_text}, {product_count}/{product_limit}"
    return line


def admin_subscriptions_keyboard(items: list[dict[str, object]]) -> InlineKeyboardMarkup | None:
    rows: list[list[InlineKeyboardButton]] = []
    for item in items[:5]:
        seller = item.get("seller") if isinstance(item.get("seller"), dict) else {}
        plans = item.get("plans") if isinstance(item.get("plans"), list) else []
        seller_id = seller.get("id")
        seller_name = seller.get("display_name") or "Автор"
        if not seller_id:
            continue
        for plan in plans[:4]:
            code = plan.get("code")
            if not code:
                continue
            rows.append([InlineKeyboardButton(text=f"{plan.get('name')}: {seller_name}", callback_data=f"admin:sub:{code}:{seller_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:dashboard")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:dashboard")],
        ]
    )


async def send_downloaded_file(message: Message, downloaded_file, *, caption: str | None = None) -> None:
    file_input = BufferedInputFile(downloaded_file.content, filename=downloaded_file.filename)
    if downloaded_file.content_type.startswith("image/"):
        await message.answer_photo(photo=file_input, caption=caption)
        return
    await message.answer_document(document=file_input, caption=caption)


async def safe_answer(callback: CallbackQuery, text: str, *, reply_markup=None) -> None:
    if callback.message is not None:
        await callback.message.answer(text, reply_markup=reply_markup)
    else:
        await callback.answer(text, show_alert=True)


@router.callback_query(F.data.startswith("admin:file:"))
async def admin_file(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    product_id = product_id_from_callback(callback.data)
    api = ApiClient()
    try:
        product = await api.admin_get_product(callback.from_user, product_id)
    except httpx.HTTPError:
        logger.exception("Failed to fetch product for admin file preview")
        await callback.message.answer("Не вдалося завантажити матеріал.", reply_markup=back_to_admin_keyboard())
        await callback.answer()
        return

    delivery_method = product.get("delivery_method")
    product_file_id = product.get("product_file_id")
    if delivery_method == "external_link":
        await callback.message.answer(
            "🔗 Автор передає матеріал через зовнішнє посилання:\n"
            f"{product.get('external_file_url') or 'посилання не вказано'}",
            reply_markup=back_to_admin_keyboard(),
        )
        await callback.answer()
        return
    if delivery_method == "private_message":
        await callback.message.answer(
            "💬 Автор позначив, що передасть файл покупцю напряму в Telegram після звернення.",
            reply_markup=back_to_admin_keyboard(),
        )
        await callback.answer()
        return
    if not product_file_id:
        await callback.message.answer("Файл матеріалу не прикріплено.", reply_markup=back_to_admin_keyboard())
        await callback.answer()
        return

    try:
        downloaded_file = await api.admin_download_file(callback.from_user, str(product_file_id))
        await send_downloaded_file(
            callback.message,
            downloaded_file,
            caption=f"👀 Файл матеріалу: {product.get('title')}",
        )
        await callback.message.answer("Дія модерації:", reply_markup=back_to_admin_keyboard())
    except Exception:
        logger.exception("Failed to download product file for admin")
        await callback.message.answer("Не вдалося отримати файл матеріалу.", reply_markup=back_to_admin_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:product:"))
async def admin_product_card(callback: CallbackQuery) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return
    product_id = product_id_from_callback(callback.data)
    try:
        product = await ApiClient().admin_get_product(callback.from_user, product_id)
    except httpx.HTTPError:
        logger.exception("Failed to fetch product card")
        await safe_answer(callback, "Не вдалося завантажити матеріал.", reply_markup=back_to_admin_keyboard())
        await callback.answer()
        return
    await safe_answer(
        callback,
        f"Матеріал: {product.get('title')}\nСтатус: {product.get('status')}",
        reply_markup=moderation_keyboard(product_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:previews:"))
async def admin_previews(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    product_id = product_id_from_callback(callback.data)
    api = ApiClient()
    try:
        product = await api.admin_get_product(callback.from_user, product_id)
    except httpx.HTTPError:
        logger.exception("Failed to fetch product for admin previews")
        await callback.message.answer("Не вдалося завантажити матеріал.", reply_markup=back_to_admin_keyboard())
        await callback.answer()
        return

    preview_file_ids = [str(file_id) for file_id in product.get("preview_file_ids", [])]
    if not preview_file_ids:
        await callback.message.answer("Превʼю не прикріплено.", reply_markup=back_to_admin_keyboard())
        await callback.answer()
        return

    for index, file_id in enumerate(preview_file_ids, start=1):
        try:
            downloaded_file = await api.admin_download_file(callback.from_user, file_id)
            await send_downloaded_file(
                callback.message,
                downloaded_file,
                caption=f"🖼 Превʼю {index}/{len(preview_file_ids)}: {product.get('title')}",
            )
        except Exception:
            logger.exception("Failed to download product preview for admin")
            await callback.message.answer(f"Не вдалося отримати превʼю {index}.")
    await callback.message.answer("Дія модерації:", reply_markup=back_to_admin_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:subscriptions")
async def admin_subscriptions(callback: CallbackQuery) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    try:
        api = ApiClient()
        subscriptions = await api.admin_list_subscriptions(callback.from_user)
        plans = [plan for plan in await api.get_subscription_plans() if int(plan.get("price_amount") or 0) > 0]
        for item in subscriptions:
            item["plans"] = plans
    except httpx.HTTPError:
        logger.exception("Failed to fetch admin subscriptions")
        await callback.message.answer("Не вдалося завантажити підписки авторів.", reply_markup=back_to_admin_keyboard())
        await callback.answer()
        return

    if not subscriptions:
        await callback.message.answer("💳 Авторських підписок ще немає.", reply_markup=back_to_admin_keyboard())
    else:
        lines = "\n".join(subscription_line(item) for item in subscriptions[:10])
        await callback.message.answer(
            f"💳 Підписки авторів\n\n{lines}",
            reply_markup=admin_subscriptions_keyboard(subscriptions),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:sub:"))
async def admin_activate_subscription(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None or not is_admin(callback.from_user.id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    _, _, plan_code, seller_id = callback.data.split(":", 3)
    api = ApiClient()
    try:
        plans = await api.get_subscription_plans()
        plan = next((item for item in plans if item.get("code") == plan_code), None)
        if plan is None:
            await callback.answer("Тариф не знайдено.", show_alert=True)
            return
        subscription = await api.admin_activate_seller_subscription(
            callback.from_user,
            seller_id=seller_id,
            plan_id=str(plan["id"]),
        )
    except httpx.HTTPError:
        logger.exception("Failed to activate seller subscription")
        await callback.message.answer("Не вдалося активувати підписку автора.", reply_markup=back_to_admin_keyboard())
        await callback.answer()
        return

    seller = subscription.get("seller") if isinstance(subscription.get("seller"), dict) else {}
    plan = subscription.get("plan") if isinstance(subscription.get("plan"), dict) else {}
    await callback.message.answer(
        "✅ Підписку автора оновлено.\n\n"
        f"Автор: {seller.get('display_name') or seller_id}\n"
        f"Тариф: {plan.get('name') or plan_code}\n"
        f"Статус: {subscription.get('status')}",
        reply_markup=back_to_admin_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:approve:"))
async def admin_approve(callback: CallbackQuery) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    if ":confirm:" not in callback.data:
        product_id = product_id_from_callback(callback.data)
        await safe_answer(
            callback,
            "Підтвердіть публікацію матеріалу. Дія одразу покаже його в каталозі.",
            reply_markup=moderation_confirm_keyboard("approve", product_id),
        )
        await callback.answer()
        return

    product_id = callback.data.rsplit(":", 1)[1]
    try:
        product = await ApiClient().admin_approve_product(callback.from_user, product_id)
    except httpx.HTTPError:
        logger.exception("Failed to approve product")
        await safe_answer(callback, "Не вдалося опублікувати матеріал.", reply_markup=back_to_admin_keyboard())
        await callback.answer()
        return

    await safe_answer(callback, f"✅ Матеріал “{product['title']}” опубліковано.", reply_markup=back_to_admin_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:hide:"))
async def admin_hide(callback: CallbackQuery) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return

    if ":confirm:" not in callback.data:
        product_id = product_id_from_callback(callback.data)
        await safe_answer(
            callback,
            "Підтвердіть приховування матеріалу. Він зникне з каталогу.",
            reply_markup=moderation_confirm_keyboard("hide", product_id),
        )
        await callback.answer()
        return

    product_id = callback.data.rsplit(":", 1)[1]
    try:
        product = await ApiClient().admin_hide_product(callback.from_user, product_id)
    except httpx.HTTPError:
        logger.exception("Failed to hide product")
        await safe_answer(callback, "Не вдалося сховати матеріал.", reply_markup=back_to_admin_keyboard())
        await callback.answer()
        return

    await safe_answer(callback, f"🙈 Матеріал “{product['title']}” сховано.", reply_markup=back_to_admin_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:reject:"))
async def admin_reject_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return
    await state.set_state(AdminModerationStates.reject_reason)
    await state.update_data(product_id=product_id_from_callback(callback.data))
    await callback.message.answer("Напишіть причину відхилення матеріалу.", reply_markup=back_to_admin_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:changes:"))
async def admin_changes_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Недостатньо прав.", show_alert=True)
        return
    await state.set_state(AdminModerationStates.changes_reason)
    await state.update_data(product_id=product_id_from_callback(callback.data))
    await callback.message.answer("Напишіть, які правки потрібні автору.", reply_markup=back_to_admin_keyboard())
    await callback.answer()


@router.message(AdminModerationStates.reject_reason)
async def admin_reject_reason(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await message.answer("Недостатньо прав.")
        await state.clear()
        return
    reason = (message.text or "").strip()
    if len(reason) < 3:
        await message.answer("Причина має містити щонайменше 3 символи.")
        return
    data = await state.get_data()
    try:
        product = await ApiClient().admin_reject_product(message.from_user, data["product_id"], reason=reason)
    except httpx.HTTPError:
        logger.exception("Failed to reject product")
        await message.answer("Не вдалося відхилити матеріал.")
        await state.clear()
        return
    await state.clear()
    await message.answer(f"❌ Матеріал “{product['title']}” відхилено.", reply_markup=back_to_admin_keyboard())


@router.message(AdminModerationStates.changes_reason)
async def admin_changes_reason(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await message.answer("Недостатньо прав.")
        await state.clear()
        return
    reason = (message.text or "").strip()
    if len(reason) < 3:
        await message.answer("Коментар має містити щонайменше 3 символи.")
        return
    data = await state.get_data()
    try:
        product = await ApiClient().admin_request_product_changes(message.from_user, data["product_id"], reason=reason)
    except httpx.HTTPError:
        logger.exception("Failed to request product changes")
        await message.answer("Не вдалося попросити правки.")
        await state.clear()
        return
    await state.clear()
    await message.answer(f"✏️ Для матеріалу “{product['title']}” запитано правки.", reply_markup=back_to_admin_keyboard())
