import logging

import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.api_client import ApiClient
from bot.config import get_settings
from bot.keyboards.seller_menu import (
    cancel_to_seller_keyboard,
    product_confirm_keyboard,
    product_file_delivery_keyboard,
    seller_menu,
)
from bot.services.admin_notifications import notify_admins_about_product
from bot.services.file_upload import upload_document_from_telegram, upload_photo_from_telegram
from bot.services.service_rules import SERVICE_RULES_SHORT
from bot.states.seller_profile import ProductCreationStates, SellerProfileStates


router = Router()
logger = logging.getLogger(__name__)

DELIVERY_UPLOADED_FILE = "uploaded_file"
DELIVERY_EXTERNAL_LINK = "external_link"
DELIVERY_PRIVATE_MESSAGE = "private_message"


def product_file_instruction() -> str:
    max_mb = get_settings().max_product_file_mb
    return (
        f"Надішліть основний файл матеріалу як документ до {max_mb} МБ.\n\n"
        "Якщо файл більший, можна додати посилання на нього або обрати варіант "
        "передати файл покупцю в приватні повідомлення після звернення."
    )


def is_external_link(text: str | None) -> bool:
    value = (text or "").strip().lower()
    return value.startswith(("https://", "http://"))


def valid_delivery_data(data: dict[str, object]) -> bool:
    delivery_method = data.get("delivery_method")
    if delivery_method == DELIVERY_UPLOADED_FILE:
        return bool(data.get("product_file_id"))
    if delivery_method == DELIVERY_EXTERNAL_LINK:
        return is_external_link(str(data.get("external_file_url") or ""))
    if delivery_method == DELIVERY_PRIVATE_MESSAGE:
        return True
    return False


@router.callback_query(F.data == "seller:add_product")
async def start_product_creation(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None:
        await callback.answer("Не вдалося визначити користувача.", show_alert=True)
        return

    await state.clear()

    try:
        profile = await ApiClient().get_seller_profile(callback.from_user)
    except httpx.HTTPError:
        logger.exception("Failed to fetch seller profile before product creation")
        await callback.message.answer(
            "Не вдалося підключитися до кабінету автора. Спробуйте ще раз трохи пізніше.",
            reply_markup=cancel_to_seller_keyboard(),
        )
        await callback.answer()
        return

    if profile is None:
        await state.set_state(SellerProfileStates.display_name)
        await callback.message.answer(
            "Перед додаванням матеріалу створімо кабінет автора.\n\n"
            f"{SERVICE_RULES_SHORT}\n\n"
            "Як вас показувати в каталозі? Напишіть імʼя або назву вашого авторського профілю.",
            reply_markup=cancel_to_seller_keyboard(),
        )
        await callback.answer()
        return

    await state.set_state(ProductCreationStates.title)
    await callback.message.answer(
        f"➕ Додамо матеріал.\n\n{SERVICE_RULES_SHORT}\n\nНапишіть назву матеріалу.",
        reply_markup=cancel_to_seller_keyboard(),
    )
    await callback.answer()


@router.message(ProductCreationStates.title)
async def product_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if len(title) < 3:
        await message.answer("Назва має містити щонайменше 3 символи.")
        return
    await state.update_data(title=title)
    await state.set_state(ProductCreationStates.description)
    await message.answer(
        "Опишіть матеріал: що всередині, для кого він і як його використовувати.",
        reply_markup=cancel_to_seller_keyboard(),
    )


@router.message(ProductCreationStates.description)
async def product_description(message: Message, state: FSMContext) -> None:
    description = (message.text or "").strip()
    if len(description) < 10:
        await message.answer("Опис має містити щонайменше 10 символів.")
        return
    await state.update_data(description=description)
    await state.set_state(ProductCreationStates.language)
    await message.answer(
        "Вкажіть мову матеріалу. Наприклад: english, german, ukrainian.",
        reply_markup=cancel_to_seller_keyboard(),
    )


@router.message(ProductCreationStates.language)
async def product_language(message: Message, state: FSMContext) -> None:
    language = (message.text or "").strip().lower()
    if len(language) < 2:
        await message.answer("Вкажіть мову матеріалу.")
        return
    await state.update_data(language=language)
    await state.set_state(ProductCreationStates.level)
    await message.answer(
        "Вкажіть рівень. Наприклад: a1, a2, b1, kids, teens, mixed.",
        reply_markup=cancel_to_seller_keyboard(),
    )


@router.message(ProductCreationStates.level)
async def product_level(message: Message, state: FSMContext) -> None:
    level = (message.text or "").strip().lower()
    await state.update_data(level=level or None)
    await state.set_state(ProductCreationStates.category)
    await message.answer(
        "Вкажіть тип матеріалу. Наприклад: worksheet, speaking_cards, test, presentation.",
        reply_markup=cancel_to_seller_keyboard(),
    )


@router.message(ProductCreationStates.category)
async def product_category(message: Message, state: FSMContext) -> None:
    category = (message.text or "").strip().lower()
    if len(category) < 2:
        await message.answer("Вкажіть тип матеріалу.")
        return
    await state.update_data(category=category)
    await state.set_state(ProductCreationStates.audience)
    await message.answer(
        "Вкажіть аудиторію. Наприклад: kids, teens, adults, business, teachers.",
        reply_markup=cancel_to_seller_keyboard(),
    )


@router.message(ProductCreationStates.audience)
async def product_audience(message: Message, state: FSMContext) -> None:
    audience = (message.text or "").strip().lower()
    await state.update_data(audience=audience or None)
    await state.set_state(ProductCreationStates.price)
    await message.answer(
        "Вкажіть ціну в гривнях цілим числом. Наприклад: 149",
        reply_markup=cancel_to_seller_keyboard(),
    )


@router.message(ProductCreationStates.price)
async def product_price(message: Message, state: FSMContext) -> None:
    raw_price = (message.text or "").strip()
    if not raw_price.isdigit():
        await message.answer("Ціна має бути цілим числом у гривнях.")
        return
    price_amount = int(raw_price) * 100
    await state.update_data(price_amount=price_amount, currency="UAH")
    await state.set_state(ProductCreationStates.product_file)
    await message.answer(product_file_instruction(), reply_markup=product_file_delivery_keyboard())


@router.message(ProductCreationStates.product_file)
async def product_file(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        await message.answer("Не вдалося визначити користувача.")
        return

    if message.document is None:
        text = (message.text or "").strip()
        if is_external_link(text):
            await state.update_data(
                product_file_id=None,
                delivery_method=DELIVERY_EXTERNAL_LINK,
                external_file_url=text,
                preview_file_ids=[],
            )
            await state.set_state(ProductCreationStates.previews)
            await message.answer(
                "Посилання збережено. Тепер надішліть 1–3 зображення-превʼю.",
                reply_markup=product_confirm_keyboard(),
            )
            return

        if text.lower() in {"особисто", "в личку", "у личку", "приватно", "private"}:
            await state.update_data(
                product_file_id=None,
                delivery_method=DELIVERY_PRIVATE_MESSAGE,
                external_file_url=None,
                preview_file_ids=[],
            )
            await state.set_state(ProductCreationStates.previews)
            await message.answer(
                "Добре, у картці буде вказано, що автор передасть файл покупцю напряму. "
                "Тепер надішліть 1–3 зображення-превʼю.",
                reply_markup=product_confirm_keyboard(),
            )
            return

        await message.answer(product_file_instruction(), reply_markup=product_file_delivery_keyboard())
        return

    max_bytes = get_settings().max_product_file_mb * 1024 * 1024
    if message.document.file_size and message.document.file_size > max_bytes:
        await message.answer(
            f"Файл більший за ліміт {get_settings().max_product_file_mb} МБ, тому ми не будемо зберігати його в сервісі.\n\n"
            "Надішліть посилання на файл або оберіть, що передасте файл покупцю в приватні повідомлення.",
            reply_markup=product_file_delivery_keyboard(),
        )
        return

    try:
        uploaded = await upload_document_from_telegram(
            bot=message.bot,
            telegram_user=message.from_user,
            document=message.document,
            file_kind="product_file",
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 413:
            await message.answer(
                f"Файл більший за ліміт {get_settings().max_product_file_mb} МБ, тому ми не будемо зберігати його в сервісі.\n\n"
                "Надішліть посилання на файл або оберіть, що передасте файл покупцю в приватні повідомлення.",
                reply_markup=product_file_delivery_keyboard(),
            )
        else:
            logger.exception("Failed to upload product file")
            await message.answer(
                "Не вдалося завантажити файл. Перевірте формат і спробуйте ще раз або оберіть інший спосіб передачі.",
                reply_markup=product_file_delivery_keyboard(),
            )
        return
    except httpx.HTTPError:
        logger.exception("Failed to upload product file")
        await message.answer(
            "Не вдалося завантажити файл. Перевірте формат і спробуйте ще раз або оберіть інший спосіб передачі.",
            reply_markup=product_file_delivery_keyboard(),
        )
        return

    await state.update_data(
        product_file_id=uploaded["id"],
        delivery_method=DELIVERY_UPLOADED_FILE,
        external_file_url=None,
        preview_file_ids=[],
    )
    await state.set_state(ProductCreationStates.previews)
    await message.answer(
        "Файл збережено. Тепер надішліть 1–3 зображення-превʼю.",
        reply_markup=product_confirm_keyboard(),
    )


@router.callback_query(F.data == "product:file_link")
async def product_file_link(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Надішліть посилання на файл. Воно має починатися з https:// або http://.",
        reply_markup=product_file_delivery_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "product:file_private")
async def product_file_private(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(
        product_file_id=None,
        delivery_method=DELIVERY_PRIVATE_MESSAGE,
        external_file_url=None,
        preview_file_ids=[],
    )
    await state.set_state(ProductCreationStates.previews)
    await callback.message.answer(
        "Добре, файл не зберігатиметься в сервісі. Автор передасть його покупцю напряму після звернення.\n\n"
        "Тепер надішліть 1–3 зображення-превʼю.",
        reply_markup=product_confirm_keyboard(),
    )
    await callback.answer()


@router.message(ProductCreationStates.previews)
async def product_previews(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.photo:
        await message.answer("Надішліть превʼю як зображення. Потрібно 1–3 превʼю.")
        return

    data = await state.get_data()
    preview_file_ids = list(data.get("preview_file_ids", []))
    if len(preview_file_ids) >= 3:
        await message.answer("Вже додано 3 превʼю. Перейдімо до підтвердження.", reply_markup=product_confirm_keyboard())
        await state.set_state(ProductCreationStates.confirm)
        return

    try:
        uploaded = await upload_photo_from_telegram(
            bot=message.bot,
            telegram_user=message.from_user,
            photo=message.photo[-1],
            filename=f"preview-{len(preview_file_ids) + 1}.jpg",
        )
    except httpx.HTTPError:
        logger.exception("Failed to upload preview")
        await message.answer(
            "Не вдалося завантажити превʼю. Спробуйте інше зображення або скасуйте створення.",
            reply_markup=product_confirm_keyboard(),
        )
        return

    preview_file_ids.append(uploaded["id"])
    await state.update_data(preview_file_ids=preview_file_ids)
    if len(preview_file_ids) < 3:
        await message.answer(
            f"Превʼю додано ({len(preview_file_ids)}/3). Надішліть ще або натисніть підтвердження.",
            reply_markup=product_confirm_keyboard(),
        )
    else:
        await state.set_state(ProductCreationStates.confirm)
        await message.answer("Додано 3 превʼю. Перейдімо до підтвердження.", reply_markup=product_confirm_keyboard())


@router.callback_query(F.data == "product:create_confirm")
async def product_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None:
        await callback.answer("Не вдалося визначити користувача.", show_alert=True)
        return

    data = await state.get_data()
    preview_file_ids = data.get("preview_file_ids", [])
    if not valid_delivery_data(data):
        await callback.message.answer(
            "Спочатку оберіть спосіб передачі матеріалу: файл, посилання або приватне повідомлення.",
            reply_markup=product_file_delivery_keyboard(),
        )
        await state.set_state(ProductCreationStates.product_file)
        await callback.answer()
        return
    if not preview_file_ids:
        await callback.message.answer("Додайте хоча б одне превʼю.")
        await callback.answer()
        return

    payload = {
        "title": data["title"],
        "description": data["description"],
        "language": data["language"],
        "level": data.get("level"),
        "category": data["category"],
        "audience": data.get("audience"),
        "price_amount": data["price_amount"],
        "currency": data["currency"],
        "product_file_id": data.get("product_file_id"),
        "delivery_method": data["delivery_method"],
        "external_file_url": data.get("external_file_url"),
        "preview_file_ids": preview_file_ids,
    }

    try:
        product = await ApiClient().create_product(callback.from_user, payload)
        product = await ApiClient().submit_product(callback.from_user, str(product["id"]))
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 403:
            await callback.message.answer("Досягнуто ліміт матеріалів для вашого тарифу.", reply_markup=seller_menu())
        elif exc.response.status_code == 404:
            await state.clear()
            await state.set_state(SellerProfileStates.display_name)
            await callback.message.answer(
                "Перед відправкою матеріалу потрібно створити кабінет автора.\n\n"
                "Як вас показувати в каталозі? Напишіть імʼя або назву вашого авторського профілю.",
                reply_markup=cancel_to_seller_keyboard(),
            )
            await callback.answer()
            return
        else:
            logger.exception("Failed to create product")
            await callback.message.answer("Не вдалося створити матеріал. Спробуйте ще раз пізніше.")
        await state.clear()
        await callback.answer()
        return
    except httpx.HTTPError:
        logger.exception("Failed to create product")
        await callback.message.answer("Не вдалося створити матеріал. Спробуйте ще раз пізніше.")
        await state.clear()
        await callback.answer()
        return

    await state.clear()
    await notify_admins_about_product(callback.bot, product)
    await callback.message.answer(
        f"✅ Матеріал “{product['title']}” відправлено на модерацію.",
        reply_markup=seller_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "product:create_cancel")
async def product_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Повертаємось назад.", reply_markup=seller_menu())
    await callback.answer()
