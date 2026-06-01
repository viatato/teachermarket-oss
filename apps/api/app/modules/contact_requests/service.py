import asyncio
from urllib import parse, request
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import Settings, get_settings
from app.db.models import AuditLog, ContactRequest, Product, SellerProfile, User
from app.modules.contact_requests.schemas import ContactRequestCreate


def seller_telegram_url(seller: SellerProfile) -> str | None:
    if seller.contact_url:
        return seller.contact_url
    if seller.contact_username:
        return f"https://t.me/{seller.contact_username.lstrip('@')}"
    return None


async def load_contactable_product(db: AsyncSession, product_id: UUID) -> Product:
    product = await db.scalar(
        select(Product)
        .options(selectinload(Product.seller).selectinload(SellerProfile.user))
        .where(Product.id == product_id, Product.status == "published")
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матеріал не знайдено.")
    return product


async def create_contact_request(
    db: AsyncSession,
    *,
    user: User,
    product_id: UUID,
    payload: ContactRequestCreate,
) -> tuple[ContactRequest, str]:
    product = await load_contactable_product(db, product_id)
    if product.seller.user_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не можна створити звернення до власного матеріалу.",
        )

    telegram_url = seller_telegram_url(product.seller)
    if telegram_url is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Автор ще не додав Telegram-контакт.",
        )

    message = payload.message.strip() if payload.message else None
    existing = await db.scalar(
        select(ContactRequest).where(
            ContactRequest.requester_id == user.id,
            ContactRequest.product_id == product.id,
        )
    )
    if existing is not None:
        if message and message != existing.message:
            existing.message = message
            await db.commit()
            await db.refresh(existing)
        return existing, telegram_url

    contact_request = ContactRequest(
        requester_id=user.id,
        product_id=product.id,
        seller_id=product.seller_id,
        requester_telegram_id=user.telegram_id,
        requester_username=user.username,
        message=message,
    )
    db.add(contact_request)
    await db.flush()

    db.add(
        AuditLog(
            actor_user_id=user.id,
            action="contact.requested",
            entity_type="contact_request",
            entity_id=contact_request.id,
            meta={
                "product_id": str(product.id),
                "seller_id": str(product.seller_id),
            },
        )
    )
    await db.commit()
    await db.refresh(contact_request)

    await notify_seller_about_contact_request(
        get_settings(),
        seller_telegram_id=product.seller.user.telegram_id,
        product_title=product.title,
        requester_user=user,
        message=message,
    )
    return contact_request, telegram_url


async def notify_seller_about_contact_request(
    settings: Settings,
    *,
    seller_telegram_id: int,
    product_title: str,
    requester_user: User,
    message: str | None,
) -> None:
    token = settings.telegram_bot_token
    if "replace_me" in token:
        return

    requester_name = requester_display_name(requester_user)
    text = (
        "📩 Нове звернення щодо матеріалу\n\n"
        f"Матеріал: {product_title}\n"
        f"Покупець: {requester_name}"
    )
    if message:
        text += f"\n\nПовідомлення: {message}"

    try:
        await asyncio.to_thread(send_telegram_message, token, seller_telegram_id, text)
    except Exception:
        return


def requester_display_name(user: User) -> str:
    if user.username:
        return f"@{user.username}"
    full_name = " ".join(part for part in (user.first_name, user.last_name) if part)
    if full_name:
        return full_name
    return str(user.telegram_id)


def send_telegram_message(token: str, chat_id: int, text: str) -> None:
    data = parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    telegram_request = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with request.urlopen(telegram_request, timeout=10):
        pass
