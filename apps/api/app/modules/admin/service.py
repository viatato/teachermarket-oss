import asyncio
import logging
from datetime import UTC, datetime, timedelta
from urllib import parse, request
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AuditLog, Product, ProductReport, SellerProfile, Subscription, SubscriptionPlan, User
from app.config import Settings, get_settings
from app.modules.subscriptions.service import ensure_subscriptions_enabled, subscription_visibility_cutoff


logger = logging.getLogger(__name__)


def ensure_reports_enabled() -> None:
    if not get_settings().feature_reports_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Функцію не знайдено.")


async def list_pending_products(db: AsyncSession) -> list[Product]:
    result = await db.scalars(
        select(Product)
        .options(selectinload(Product.previews), selectinload(Product.seller).selectinload(SellerProfile.user))
        .where(Product.status == "pending_moderation")
        .order_by(Product.created_at.asc())
    )
    return list(result)


async def list_admin_products(
    db: AsyncSession,
    *,
    product_status: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Product], int]:
    filters = []
    if product_status:
        filters.append(Product.status == product_status)
    total = await db.scalar(select(func.count(Product.id)).where(*filters))
    products = list(
        await db.scalars(
            select(Product)
            .options(selectinload(Product.previews), selectinload(Product.seller).selectinload(SellerProfile.user))
            .where(*filters)
            .order_by(Product.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    )
    return products, total or 0


async def get_product_for_moderation(db: AsyncSession, product_id: UUID) -> Product:
    product = await db.scalar(
        select(Product)
        .options(selectinload(Product.previews), selectinload(Product.seller).selectinload(SellerProfile.user))
        .where(Product.id == product_id)
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матеріал не знайдено.")
    return product


async def write_audit_log(
    db: AsyncSession,
    *,
    actor: User,
    action: str,
    product: Product,
    meta: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action=action,
            entity_type="product",
            entity_id=product.id,
            meta=meta,
        )
    )


async def approve_product(db: AsyncSession, *, actor: User, product_id: UUID) -> Product:
    product = await get_product_for_moderation(db, product_id)
    if product.status != "pending_moderation":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Матеріал не очікує модерації.")
    product.status = "published"
    product.rejection_reason = None
    product.published_at = datetime.now(UTC)
    await write_audit_log(db, actor=actor, action="product.approved", product=product)
    await db.commit()
    product = await get_product_for_moderation(db, product.id)
    await notify_author_about_moderation(product, action="approved")
    return product


async def reject_product(db: AsyncSession, *, actor: User, product_id: UUID, reason: str) -> Product:
    product = await get_product_for_moderation(db, product_id)
    if product.status != "pending_moderation":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Матеріал не можна відхилити.")
    product.status = "rejected"
    product.rejection_reason = reason.strip()
    await write_audit_log(db, actor=actor, action="product.rejected", product=product, meta={"reason": reason.strip()})
    await db.commit()
    product = await get_product_for_moderation(db, product.id)
    await notify_author_about_moderation(product, action="rejected", reason=reason.strip())
    return product


async def request_product_changes(db: AsyncSession, *, actor: User, product_id: UUID, reason: str) -> Product:
    product = await get_product_for_moderation(db, product_id)
    if product.status != "pending_moderation":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Матеріал не очікує модерації.")
    product.status = "rejected"
    product.rejection_reason = reason.strip()
    await write_audit_log(
        db,
        actor=actor,
        action="product.changes_requested",
        product=product,
        meta={"reason": reason.strip()},
    )
    await db.commit()
    product = await get_product_for_moderation(db, product.id)
    await notify_author_about_moderation(product, action="changes_requested", reason=reason.strip())
    return product


async def hide_product(db: AsyncSession, *, actor: User, product_id: UUID) -> Product:
    product = await get_product_for_moderation(db, product_id)
    if product.status != "published":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Можна сховати лише опублікований матеріал.")
    product.status = "hidden"
    await write_audit_log(db, actor=actor, action="admin.hide_product", product=product)
    await db.commit()
    product = await get_product_for_moderation(db, product.id)
    await notify_author_about_moderation(product, action="hidden")
    return product


async def restore_product(db: AsyncSession, *, actor: User, product_id: UUID) -> Product:
    product = await get_product_for_moderation(db, product_id)
    if product.status != "hidden":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Можна відновити лише прихований матеріал.")
    product.status = "published"
    product.rejection_reason = None
    if product.published_at is None:
        product.published_at = datetime.now(UTC)
    await write_audit_log(db, actor=actor, action="product.restored", product=product)
    await db.commit()
    return await get_product_for_moderation(db, product.id)


async def notify_author_about_moderation(
    product: Product,
    *,
    action: str,
    reason: str | None = None,
    settings: Settings | None = None,
) -> None:
    current_settings = settings or get_settings()
    if "replace_me" in current_settings.telegram_bot_token:
        return

    try:
        seller_user = product.seller.user
        text = moderation_notification_text(product, action=action, reason=reason)
        await asyncio.to_thread(send_telegram_message, current_settings.telegram_bot_token, seller_user.telegram_id, text)
    except Exception:
        logger.exception("Failed to notify author about moderation result", extra={"product_id": str(product.id)})


def moderation_notification_text(product: Product, *, action: str, reason: str | None = None) -> str:
    if action == "approved":
        return f"✅ Ваш матеріал “{product.title}” опубліковано в каталозі ТічерМаркет."
    if action == "rejected":
        text = f"❌ Матеріал “{product.title}” відхилено модерацією."
    elif action == "changes_requested":
        text = f"✏️ Для матеріалу “{product.title}” потрібні правки."
    elif action == "hidden":
        text = f"🙈 Матеріал “{product.title}” приховано з каталогу."
    else:
        text = f"Оновлено статус матеріалу “{product.title}”."

    if reason:
        text += f"\n\nКоментар модератора: {reason}"
    return text


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


async def list_admin_subscription_states(db: AsyncSession) -> list[tuple[SellerProfile, Subscription | None, int, int]]:
    ensure_subscriptions_enabled()
    sellers = list(
        await db.scalars(
            select(SellerProfile)
            .options(selectinload(SellerProfile.user))
            .where(SellerProfile.status == "active")
            .order_by(SellerProfile.created_at.desc())
        )
    )
    states: list[tuple[SellerProfile, Subscription | None, int, int]] = []
    for seller in sellers:
        subscription = await get_best_active_subscription(db, seller.id)
        product_count = await db.scalar(
            select(func.count(Product.id)).where(
                Product.seller_id == seller.id,
                Product.status.in_(("published", "pending_moderation")),
            )
        )
        product_limit = subscription.plan.product_limit if subscription and subscription.plan else 0
        states.append((seller, subscription, product_count or 0, product_limit))
    return states


async def get_best_active_subscription(db: AsyncSession, seller_id: UUID) -> Subscription | None:
    now = datetime.now(UTC)
    return await db.scalar(
        select(Subscription)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .options(selectinload(Subscription.plan))
        .where(
            Subscription.seller_id == seller_id,
            Subscription.status.in_(("active", "trial")),
            (Subscription.expires_at.is_(None)) | (Subscription.expires_at >= subscription_visibility_cutoff(now)),
        )
        .order_by(SubscriptionPlan.product_limit.desc(), Subscription.expires_at.desc().nullslast())
        .limit(1)
    )


async def activate_seller_subscription(
    db: AsyncSession,
    *,
    actor: User,
    seller_id: UUID,
    plan_id: UUID,
    duration_days: int | None = None,
) -> Subscription:
    ensure_subscriptions_enabled()
    seller = await db.scalar(select(SellerProfile).where(SellerProfile.id == seller_id))
    if seller is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автора не знайдено.")

    plan = await db.scalar(
        select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id, SubscriptionPlan.is_active.is_(True))
    )
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не знайдено.")

    now = datetime.now(UTC)
    await expire_stale_and_conflicting_subscriptions(db, seller.id)
    subscription = await get_best_active_subscription(db, seller.id)
    days = duration_days or plan.duration_days
    if subscription is None:
        subscription = Subscription(
            seller_id=seller.id,
            plan_id=plan.id,
            status="active",
            starts_at=now,
            expires_at=now + timedelta(days=days),
        )
        db.add(subscription)
        await db.flush()
    else:
        base_time = subscription.expires_at if subscription.expires_at and subscription.expires_at > now else now
        subscription.plan_id = plan.id
        subscription.status = "active"
        subscription.expires_at = base_time + timedelta(days=days)
        await db.flush()

    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action="admin.subscription_activated",
            entity_type="subscription",
            entity_id=subscription.id,
            meta={
                "seller_id": str(seller.id),
                "plan_id": str(plan.id),
                "duration_days": days,
            },
        )
    )
    await db.commit()
    refreshed = await db.scalar(
        select(Subscription)
        .options(selectinload(Subscription.plan), selectinload(Subscription.seller))
        .where(Subscription.id == subscription.id)
    )
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Підписку не знайдено.")
    return refreshed


async def expire_stale_and_conflicting_subscriptions(db: AsyncSession, seller_id: UUID) -> None:
    now = datetime.now(UTC)
    stale = list(
        await db.scalars(
            select(Subscription).where(
                Subscription.seller_id == seller_id,
                Subscription.status.in_(("active", "trial")),
                Subscription.expires_at.is_not(None),
                Subscription.expires_at < subscription_visibility_cutoff(now),
            )
        )
    )
    for subscription in stale:
        subscription.status = "expired"


async def list_subscription_plans(db: AsyncSession, *, include_inactive: bool = False) -> list[SubscriptionPlan]:
    ensure_subscriptions_enabled()
    filters = [] if include_inactive else [SubscriptionPlan.is_active.is_(True)]
    return list(
        await db.scalars(
            select(SubscriptionPlan)
            .where(*filters)
            .order_by(SubscriptionPlan.price_amount.asc(), SubscriptionPlan.created_at.asc())
        )
    )


async def create_subscription_plan(
    db: AsyncSession,
    *,
    actor: User,
    payload,
) -> SubscriptionPlan:
    ensure_subscriptions_enabled()
    plan = SubscriptionPlan(
        code=payload.code.strip().lower(),
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        price_amount=payload.price_amount,
        currency=payload.currency.upper(),
        duration_days=payload.duration_days,
        product_limit=payload.product_limit,
        is_active=payload.is_active,
    )
    db.add(plan)
    await db.flush()
    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action="subscription_plan.created",
            entity_type="subscription_plan",
            entity_id=plan.id,
        )
    )
    await db.commit()
    await db.refresh(plan)
    return plan


async def update_subscription_plan(
    db: AsyncSession,
    *,
    actor: User,
    plan_id: UUID,
    payload,
) -> SubscriptionPlan:
    ensure_subscriptions_enabled()
    plan = await db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не знайдено.")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        if field == "code" and value:
            value = value.lower()
        if field == "currency" and value:
            value = value.upper()
        setattr(plan, field, value)
    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action="subscription_plan.updated",
            entity_type="subscription_plan",
            entity_id=plan.id,
            meta={"fields": sorted(update_data.keys())},
        )
    )
    await db.commit()
    await db.refresh(plan)
    return plan


async def deactivate_subscription_plan(db: AsyncSession, *, actor: User, plan_id: UUID) -> SubscriptionPlan:
    ensure_subscriptions_enabled()
    plan = await db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не знайдено.")
    plan.is_active = False
    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action="subscription_plan.deactivated",
            entity_type="subscription_plan",
            entity_id=plan.id,
        )
    )
    await db.commit()
    await db.refresh(plan)
    return plan


async def update_seller_status(db: AsyncSession, *, actor: User, seller_id: UUID, new_status: str) -> SellerProfile:
    seller = await db.scalar(select(SellerProfile).options(selectinload(SellerProfile.user)).where(SellerProfile.id == seller_id))
    if seller is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автора не знайдено.")
    seller.status = new_status
    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action="seller.status_updated",
            entity_type="seller_profile",
            entity_id=seller.id,
            meta={"status": new_status},
        )
    )
    await db.commit()
    refreshed = await db.scalar(select(SellerProfile).options(selectinload(SellerProfile.user)).where(SellerProfile.id == seller.id))
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автора не знайдено.")
    return refreshed


async def update_user_blocked(db: AsyncSession, *, actor: User, user_id: UUID, is_blocked: bool) -> User:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувача не знайдено.")
    user.is_blocked = is_blocked
    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action="user.blocked_updated",
            entity_type="user",
            entity_id=user.id,
            meta={"is_blocked": is_blocked},
        )
    )
    await db.commit()
    await db.refresh(user)
    return user


async def list_product_reports(db: AsyncSession, *, report_status: str | None = None) -> list[ProductReport]:
    ensure_reports_enabled()
    filters = []
    if report_status:
        filters.append(ProductReport.status == report_status)
    return list(
        await db.scalars(
            select(ProductReport)
            .options(selectinload(ProductReport.product))
            .where(*filters)
            .order_by(ProductReport.created_at.desc())
        )
    )


async def resolve_product_report(db: AsyncSession, *, actor: User, report_id: UUID) -> ProductReport:
    ensure_reports_enabled()
    report = await db.scalar(
        select(ProductReport).options(selectinload(ProductReport.product)).where(ProductReport.id == report_id)
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Скаргу не знайдено.")
    report.status = "resolved"
    report.resolved_by_user_id = actor.id
    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action="product_report.resolved",
            entity_type="product_report",
            entity_id=report.id,
        )
    )
    await db.commit()
    refreshed = await db.scalar(
        select(ProductReport).options(selectinload(ProductReport.product)).where(ProductReport.id == report.id)
    )
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Скаргу не знайдено.")
    return refreshed
