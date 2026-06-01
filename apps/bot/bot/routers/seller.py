import logging

import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.api_client import ApiClient
from bot.config import get_settings
from bot.keyboards.seller_menu import back_to_seller_keyboard, cancel_to_seller_keyboard, seller_menu
from bot.services.service_rules import SERVICE_RULES_TEXT
from bot.states.seller_profile import SellerProfileStates


router = Router()
logger = logging.getLogger(__name__)


STATUS_LABELS = {
    "draft": "чернетка",
    "pending_moderation": "на модерації",
    "published": "опубліковано",
    "rejected": "потрібні правки",
    "hidden": "приховано",
    "free": "безкоштовний",
    "active": "активна",
    "trial": "пробний період",
}


def format_price(price_amount: object, currency: object) -> str:
    amount = int(price_amount or 0) // 100
    return f"{amount} {'грн' if currency == 'UAH' else currency}"


def is_admin(user_id: int | None) -> bool:
    return bool(user_id and user_id in get_settings().admin_ids)


def product_line(product: dict[str, object]) -> str:
    status = STATUS_LABELS.get(str(product.get("status")), str(product.get("status") or ""))
    return f"• {product.get('title')} — {status}, {format_price(product.get('price_amount'), product.get('currency'))}"


def contact_request_line(contact_request: dict[str, object]) -> str:
    requester = (
        contact_request.get("requester_display_name")
        or contact_request.get("requester_username")
        or "Покупець"
    )
    text = f"• {requester}: {contact_request.get('product_title')}"
    if contact_request.get("message"):
        text += f"\n  “{contact_request['message']}”"
    return text


def subscription_plans_keyboard(plans: list[dict[str, object]]) -> InlineKeyboardMarkup | None:
    buttons: list[list[InlineKeyboardButton]] = []
    for plan in plans:
        if int(plan.get("price_amount") or 0) <= 0:
            continue
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"💳 {plan.get('name')}",
                    callback_data=f"seller:checkout:{plan.get('code')}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="seller:dashboard")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "seller:dashboard")
async def seller_dashboard(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.from_user is None:
        await callback.answer("Не вдалося визначити користувача.", show_alert=True)
        return

    try:
        profile = await ApiClient().get_seller_profile(callback.from_user)
    except httpx.HTTPError:
        logger.exception("Failed to fetch seller profile")
        await callback.message.answer(
            "Не вдалося підключитися до кабінету автора. Спробуйте ще раз трохи пізніше.",
            reply_markup=back_to_seller_keyboard(),
        )
        await callback.answer()
        return

    if profile is None:
        await state.set_state(SellerProfileStates.display_name)
        await callback.message.answer(
            "👤 Створімо кабінет автора.\n\n"
            "Як вас показувати в каталозі? Напишіть імʼя або назву вашого авторського профілю.",
            reply_markup=cancel_to_seller_keyboard(),
        )
    else:
        await callback.message.answer(
            f"👤 Кабінет автора\n\nВітаємо, {profile['display_name']}!\n\n"
            "ТічерМаркет допомагає показувати матеріали й отримувати звернення. "
            "Оплата конкретного матеріалу та передача доступу узгоджуються напряму між покупцем і автором.",
            reply_markup=seller_menu(),
        )
    await callback.answer()


@router.callback_query(F.data == "seller:rules")
async def seller_rules(callback: CallbackQuery) -> None:
    await callback.message.answer(SERVICE_RULES_TEXT, reply_markup=back_to_seller_keyboard())
    await callback.answer()


@router.message(SellerProfileStates.display_name)
async def seller_profile_display_name(message: Message, state: FSMContext) -> None:
    display_name = (message.text or "").strip()
    if len(display_name) < 2:
        await message.answer("Назва профілю має містити щонайменше 2 символи.")
        return

    await state.update_data(display_name=display_name)
    await state.set_state(SellerProfileStates.bio)
    await message.answer(
        "Коротко опишіть себе як автора.\n\n"
        "Наприклад: “Викладачка англійської, створюю speaking activities для підлітків”.",
        reply_markup=cancel_to_seller_keyboard(),
    )


@router.message(SellerProfileStates.bio)
async def seller_profile_bio(message: Message, state: FSMContext) -> None:
    bio = (message.text or "").strip()
    await state.update_data(bio=bio or None)
    await state.set_state(SellerProfileStates.contact_username)
    await message.answer(
        "Вкажіть ваш Telegram username для звʼязку без @.\n\n"
        "Наприклад: maria_teacher",
        reply_markup=cancel_to_seller_keyboard(),
    )


@router.callback_query(F.data == "seller:profile_cancel")
async def seller_profile_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Повертаємось назад.", reply_markup=seller_menu())
    await callback.answer()


@router.message(SellerProfileStates.contact_username)
async def seller_profile_contact(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        await message.answer("Не вдалося визначити користувача. Спробуйте ще раз.")
        await state.clear()
        return

    contact_username = (message.text or "").strip().removeprefix("@")
    if not contact_username:
        await message.answer("Будь ласка, вкажіть Telegram username для звʼязку.")
        return

    data = await state.get_data()
    try:
        profile = await ApiClient().create_seller_profile(
            message.from_user,
            display_name=data["display_name"],
            bio=data.get("bio"),
            contact_username=contact_username,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 409:
            await message.answer("Профіль автора вже існує.", reply_markup=seller_menu())
        else:
            logger.exception("Failed to create seller profile")
            await message.answer("Не вдалося створити профіль автора. Спробуйте ще раз пізніше.")
        await state.clear()
        return
    except httpx.HTTPError:
        logger.exception("Failed to create seller profile")
        await message.answer("Не вдалося створити профіль автора. Спробуйте ще раз пізніше.")
        await state.clear()
        return

    await state.clear()
    await message.answer(
        f"✅ Кабінет автора створено.\n\nВітаємо, {profile['display_name']}!",
        reply_markup=seller_menu(),
    )


@router.callback_query(F.data == "seller:products")
async def seller_products(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer("Не вдалося визначити користувача.", show_alert=True)
        return

    try:
        products = await ApiClient().get_seller_products(callback.from_user)
    except httpx.HTTPError:
        logger.exception("Failed to fetch seller products")
        await callback.message.answer("Не вдалося завантажити матеріали. Спробуйте ще раз пізніше.")
        await callback.answer()
        return

    if not products:
        await callback.message.answer("📦 У вас ще немає матеріалів.", reply_markup=back_to_seller_keyboard())
    else:
        lines = "\n".join(product_line(product) for product in products[:10])
        await callback.message.answer(f"📦 Мої матеріали\n\n{lines}", reply_markup=back_to_seller_keyboard())
    await callback.answer()


@router.callback_query(F.data == "seller:requests")
async def seller_requests(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer("Не вдалося визначити користувача.", show_alert=True)
        return

    try:
        contact_requests = await ApiClient().get_seller_contact_requests(callback.from_user)
    except httpx.HTTPError:
        logger.exception("Failed to fetch seller contact requests")
        await callback.message.answer("Не вдалося завантажити звернення. Спробуйте ще раз пізніше.")
        await callback.answer()
        return

    if not contact_requests:
        await callback.message.answer("📩 Нових звернень немає.", reply_markup=back_to_seller_keyboard())
    else:
        lines = "\n\n".join(contact_request_line(item) for item in contact_requests[:10])
        await callback.message.answer(f"📩 Звернення\n\n{lines}", reply_markup=back_to_seller_keyboard())
    await callback.answer()


@router.callback_query(F.data == "seller:subscription")
async def seller_subscription(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer("Не вдалося визначити користувача.", show_alert=True)
        return

    try:
        api = ApiClient()
        subscription = await api.get_seller_subscription(callback.from_user)
        plans = await api.get_subscription_plans()
    except httpx.HTTPError:
        logger.exception("Failed to fetch seller subscription")
        await callback.message.answer("Не вдалося завантажити підписку. Спробуйте ще раз пізніше.")
        await callback.answer()
        return

    plan = subscription.get("plan") or {}
    plan_name = plan.get("name") if isinstance(plan, dict) else None
    status = STATUS_LABELS.get(str(subscription.get("status")), str(subscription.get("status") or ""))
    await callback.message.answer(
        "💳 Підписка\n\n"
        f"Тариф: {plan_name or 'Free'}\n"
        f"Статус: {status}\n"
        f"Матеріали: {subscription.get('product_count')}/{subscription.get('product_limit')}\n\n"
        "У закритому тесті реальні списання не проводяться: mock-підписку підтверджує адмін.",
        reply_markup=subscription_plans_keyboard(plans),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("seller:checkout:"))
async def seller_subscription_checkout(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None:
        await callback.answer("Не вдалося визначити користувача.", show_alert=True)
        return

    plan_code = callback.data.rsplit(":", 1)[-1]
    api = ApiClient()
    try:
        plans = await api.get_subscription_plans()
        plan = next((item for item in plans if item.get("code") == plan_code), None)
        if plan is None:
            await callback.answer("Тариф не знайдено.", show_alert=True)
            return
        payment = await api.create_subscription_checkout(callback.from_user, plan_id=str(plan["id"]))
    except httpx.HTTPError:
        logger.exception("Failed to create subscription checkout")
        await callback.message.answer("Не вдалося створити mock-платіж. Спробуйте ще раз пізніше.")
        await callback.answer()
        return

    if is_admin(callback.from_user.id):
        await callback.message.answer(
            "✅ Mock-оплату створено.\n\n"
            f"Сума: {format_price(payment.get('amount'), payment.get('currency'))}\n"
            f"Dev URL: {payment.get('payment_url')}\n\n"
            "Це тестовий режим без реального списання коштів.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Позначити mock paid",
                            callback_data=f"seller:mock_paid:{payment['id']}",
                        )
                    ],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="seller:subscription")],
                ]
            ),
        )
    else:
        await callback.message.answer(
            "✅ Mock-оплату створено.\n\n"
            f"Сума: {format_price(payment.get('amount'), payment.get('currency'))}\n"
            "У закритому тесті її підтвердить адмін. Реальні списання не проводяться.",
            reply_markup=back_to_seller_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("seller:mock_paid:"))
async def seller_subscription_mock_paid(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None:
        await callback.answer("Платіж не знайдено.", show_alert=True)
        return
    if not is_admin(callback.from_user.id):
        await callback.answer("Mock-оплату підтверджує адмін.", show_alert=True)
        return

    payment_id = callback.data.rsplit(":", 1)[-1]
    try:
        payment = await ApiClient().mark_mock_payment_paid(callback.from_user, payment_id)
    except httpx.HTTPError:
        logger.exception("Failed to mark mock subscription payment paid")
        await callback.message.answer("Не вдалося підтвердити mock-оплату. Спробуйте ще раз пізніше.")
        await callback.answer()
        return

    await callback.message.answer(
        "✅ Підписку активовано.\n\n"
        f"Статус платежу: {payment.get('status')}\n"
        f"Subscription ID: {payment.get('subscription_id')}",
        reply_markup=back_to_seller_keyboard(),
    )
    await callback.answer()
