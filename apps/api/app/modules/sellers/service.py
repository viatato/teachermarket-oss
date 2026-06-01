from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from uuid import UUID

from app.db.models import AuditLog, ContactRequest, Product, ProductViewEvent, Review, SellerProfile, Subscription, SubscriptionPlan, User
from app.modules.sellers.schemas import SellerProfileCreate, SellerProfileUpdate


def telegram_contact_url(username: str | None) -> str | None:
    if not username:
        return None
    return f"https://t.me/{username}"


async def get_seller_profile(db: AsyncSession, user: User) -> SellerProfile | None:
    return await db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))


async def require_seller_profile(db: AsyncSession, user: User) -> SellerProfile:
    profile = await get_seller_profile(db, user)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профіль автора ще не створено.",
        )
    return profile


async def create_seller_profile(
    db: AsyncSession,
    user: User,
    payload: SellerProfileCreate,
) -> SellerProfile:
    existing = await get_seller_profile(db, user)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Профіль автора вже існує.",
        )

    profile = SellerProfile(
        user_id=user.id,
        display_name=payload.display_name.strip(),
        bio=payload.bio.strip() if payload.bio else None,
        contact_username=payload.contact_username,
        contact_url=telegram_contact_url(payload.contact_username),
        status="active",
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_seller_profile(
    db: AsyncSession,
    user: User,
    payload: SellerProfileUpdate,
) -> SellerProfile:
    profile = await get_seller_profile(db, user)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профіль автора ще не створено.",
        )

    if payload.display_name is not None:
        profile.display_name = payload.display_name.strip()
    if payload.bio is not None:
        profile.bio = payload.bio.strip() or None
    if payload.contact_username is not None:
        profile.contact_username = payload.contact_username
        profile.contact_url = telegram_contact_url(payload.contact_username)

    await db.commit()
    await db.refresh(profile)
    return profile


async def list_seller_products(db: AsyncSession, user: User) -> list[Product]:
    profile = await require_seller_profile(db, user)
    result = await db.scalars(
        select(Product)
        .options(selectinload(Product.previews))
        .where(Product.seller_id == profile.id)
        .order_by(Product.created_at.desc())
    )
    return list(result)


async def list_seller_contact_requests(db: AsyncSession, user: User) -> list[ContactRequest]:
    profile = await require_seller_profile(db, user)
    result = await db.scalars(
        select(ContactRequest)
        .options(selectinload(ContactRequest.product), selectinload(ContactRequest.requester))
        .where(ContactRequest.seller_id == profile.id)
        .order_by(ContactRequest.created_at.desc())
    )
    return list(result)


async def update_seller_contact_request(
    db: AsyncSession,
    user: User,
    contact_request_id: UUID,
    new_status: str,
) -> ContactRequest:
    profile = await require_seller_profile(db, user)
    contact_request = await db.scalar(
        select(ContactRequest)
        .options(selectinload(ContactRequest.product), selectinload(ContactRequest.requester))
        .where(ContactRequest.id == contact_request_id, ContactRequest.seller_id == profile.id)
    )
    if contact_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Звернення не знайдено.")
    contact_request.status = new_status
    db.add(
        AuditLog(
            actor_user_id=user.id,
            action="contact_request.status_updated",
            entity_type="contact_request",
            entity_id=contact_request.id,
            meta={"status": new_status},
        )
    )
    await db.commit()
    refreshed = await db.scalar(
        select(ContactRequest)
        .options(selectinload(ContactRequest.product), selectinload(ContactRequest.requester))
        .where(ContactRequest.id == contact_request.id)
    )
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Звернення не знайдено.")
    return refreshed


async def get_seller_subscription_state(
    db: AsyncSession,
    user: User,
) -> tuple[Subscription | None, int, int]:
    profile = await require_seller_profile(db, user)
    product_count = await db.scalar(
        select(func.count(Product.id)).where(
            Product.seller_id == profile.id,
            Product.status.in_(("published", "pending_moderation")),
        )
    )

    now = datetime.now(UTC)
    subscription = await db.scalar(
        select(Subscription)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .options(selectinload(Subscription.plan))
        .where(
            Subscription.seller_id == profile.id,
            Subscription.status.in_(("active", "trial")),
            (Subscription.expires_at.is_(None)) | (Subscription.expires_at > now),
        )
        .order_by(SubscriptionPlan.product_limit.desc(), Subscription.expires_at.desc().nullslast())
        .limit(1)
    )
    product_limit = (
        subscription.plan.product_limit if subscription and subscription.plan else get_settings().default_free_product_limit
    )
    return subscription, product_count or 0, product_limit


async def get_seller_stats(db: AsyncSession, user: User) -> dict:
    profile = await require_seller_profile(db, user)
    status_rows = await db.execute(
        select(Product.status, func.count(Product.id))
        .where(Product.seller_id == profile.id)
        .group_by(Product.status)
    )
    products_by_status = {status: count for status, count in status_rows.all()}

    contacts_total = await db.scalar(select(func.count(ContactRequest.id)).where(ContactRequest.seller_id == profile.id))
    contacts_new = await db.scalar(
        select(func.count(ContactRequest.id)).where(ContactRequest.seller_id == profile.id, ContactRequest.status == "new")
    )
    product_ids = select(Product.id).where(Product.seller_id == profile.id)
    reviews_total = await db.scalar(select(func.count(Review.id)).where(Review.product_id.in_(product_ids)))
    average_rating = await db.scalar(select(func.avg(Review.rating)).where(Review.product_id.in_(product_ids)))
    views_total = await db.scalar(select(func.count(ProductViewEvent.id)).where(ProductViewEvent.product_id.in_(product_ids)))
    views_7d = await db.scalar(
        select(func.count(ProductViewEvent.id)).where(
            ProductViewEvent.product_id.in_(product_ids),
            ProductViewEvent.created_at >= datetime.now(UTC) - timedelta(days=7),
        )
    )

    return {
        "products_by_status": products_by_status,
        "contacts_total": contacts_total or 0,
        "contacts_new": contacts_new or 0,
        "reviews_total": reviews_total or 0,
        "average_rating": float(average_rating) if average_rating is not None else None,
        "views_total": views_total or 0,
        "views_7d": views_7d or 0,
    }
