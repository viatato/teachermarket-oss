from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.models import AuditLog, SellerProfile, Subscription, SubscriptionPayment, SubscriptionPlan, User
from app.modules.sellers.service import require_seller_profile
from app.modules.subscriptions.schemas import SubscriptionCheckoutCreate
from app.services.payments.base import PaymentWebhookEvent
from app.services.payments.registry import get_payment_provider
from app.services.payments.states import (
    PAYMENT_CREATED,
    PAYMENT_PAID,
    canonical_payment_status,
    payment_transition_allowed,
)


SUBSCRIPTION_VISIBILITY_GRACE_PERIOD = timedelta(days=7)


def ensure_subscriptions_enabled() -> None:
    if not get_settings().feature_subscriptions_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Функцію не знайдено.")


def subscription_visibility_cutoff(now: datetime) -> datetime:
    return now - SUBSCRIPTION_VISIBILITY_GRACE_PERIOD


def subscription_is_visible_at(expires_at: datetime | None, now: datetime) -> bool:
    return expires_at is None or expires_at >= subscription_visibility_cutoff(now)


def subscription_should_expire_at(expires_at: datetime | None, now: datetime) -> bool:
    return expires_at is not None and expires_at < subscription_visibility_cutoff(now)


async def list_active_plans(db: AsyncSession) -> list[SubscriptionPlan]:
    ensure_subscriptions_enabled()
    result = await db.scalars(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.price_amount.asc(), SubscriptionPlan.duration_days.asc())
    )
    return list(result)


async def get_active_paid_subscription(db: AsyncSession, seller: SellerProfile) -> Subscription | None:
    ensure_subscriptions_enabled()
    now = datetime.now(UTC)
    return await db.scalar(
        select(Subscription)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .options(selectinload(Subscription.plan))
        .where(
            Subscription.seller_id == seller.id,
            Subscription.status.in_(("active", "trial")),
            SubscriptionPlan.price_amount > 0,
            (Subscription.expires_at.is_(None)) | (Subscription.expires_at >= subscription_visibility_cutoff(now)),
        )
        .order_by(Subscription.expires_at.desc().nullslast(), Subscription.created_at.desc())
        .limit(1)
    )


async def create_subscription_checkout(
    db: AsyncSession,
    *,
    user: User,
    payload: SubscriptionCheckoutCreate,
) -> SubscriptionPayment:
    ensure_subscriptions_enabled()
    seller = await require_seller_profile(db, user)
    plan = await db.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.id == payload.plan_id,
            SubscriptionPlan.is_active.is_(True),
        )
    )
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не знайдено.")
    if plan.price_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Безкоштовний тариф не потребує оплати.",
        )

    await expire_stale_subscriptions(db, seller.id)
    settings = get_settings()
    provider = get_payment_provider(settings.payment_provider)
    payment = SubscriptionPayment(
        seller_id=seller.id,
        plan_id=plan.id,
        provider=provider.code,
        amount=plan.price_amount,
        currency=plan.currency,
        status=PAYMENT_CREATED,
        raw_payload={"plan_code": plan.code},
    )
    db.add(payment)
    await db.flush()
    created_payment = provider.create_payment(payment, settings)
    payment.provider_payment_id = created_payment.provider_payment_id
    payment.payment_url = created_payment.payment_url
    db.add(
        AuditLog(
            actor_user_id=user.id,
            action="subscription.checkout_created",
            entity_type="subscription_payment",
            entity_id=payment.id,
            meta={"plan_id": str(plan.id), "provider": provider.code},
        )
    )
    await db.commit()
    return await load_payment(db, payment.id)


async def load_payment(db: AsyncSession, payment_id: UUID) -> SubscriptionPayment:
    payment = await db.scalar(
        select(SubscriptionPayment)
        .options(selectinload(SubscriptionPayment.plan), selectinload(SubscriptionPayment.subscription))
        .where(SubscriptionPayment.id == payment_id)
    )
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платіж не знайдено.")
    return payment


async def mark_mock_payment_paid(db: AsyncSession, *, payment_id: UUID, actor: User) -> SubscriptionPayment:
    ensure_subscriptions_enabled()
    payment = await load_payment(db, payment_id)
    if payment.provider != "mock":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Цей endpoint доступний лише для mock-платежів.",
        )
    if payment.status == PAYMENT_PAID:
        return payment
    if not payment_transition_allowed(payment.status, PAYMENT_PAID):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Платіж не можна оплатити в поточному статусі.",
        )

    subscription = await activate_or_extend_subscription(db, payment)
    payment.status = PAYMENT_PAID
    payment.subscription_id = subscription.id
    payment.raw_payload = {
        **(payment.raw_payload or {}),
        "mock_paid_at": datetime.now(UTC).isoformat(),
    }
    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action="subscription.payment_mock_paid",
            entity_type="subscription_payment",
            entity_id=payment.id,
            meta={"subscription_id": str(subscription.id), "plan_id": str(payment.plan_id)},
        )
    )
    await db.commit()
    return await load_payment(db, payment.id)


async def process_payment_webhook(
    db: AsyncSession,
    *,
    provider_code: str,
    raw_body: bytes,
    headers: dict[str, str],
) -> tuple[SubscriptionPayment, dict | None]:
    ensure_subscriptions_enabled()
    settings = get_settings()
    provider = get_payment_provider(provider_code)
    provider.verify_webhook(raw_body=raw_body, headers=headers, settings=settings)
    event = provider.parse_event(raw_body=raw_body)

    payment = await load_payment_by_provider_id(db, provider_code=provider.code, provider_payment_id=event.provider_payment_id)
    validate_webhook_event(payment, event)
    target_status = canonical_payment_status(event.status)
    if target_status is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Непідтримуваний статус платежу.")

    if payment.status == PAYMENT_PAID or payment.status == target_status:
        return payment, event.response_payload
    if not payment_transition_allowed(payment.status, target_status):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Перехід між статусами платежу заборонено.",
        )

    if target_status == PAYMENT_PAID:
        subscription = await activate_or_extend_subscription(db, payment)
        payment.status = PAYMENT_PAID
        payment.subscription_id = subscription.id
        payment.raw_payload = {
            **(payment.raw_payload or {}),
            "webhook": event.raw_payload,
            "webhook_paid_at": datetime.now(UTC).isoformat(),
        }
        db.add(
            AuditLog(
                actor_user_id=None,
                action="subscription.webhook_paid",
                entity_type="subscription_payment",
                entity_id=payment.id,
                meta={"provider": provider.code, "subscription_id": str(subscription.id)},
            )
        )
    else:
        payment.status = target_status
        payment.raw_payload = {**(payment.raw_payload or {}), "webhook": event.raw_payload}
        db.add(
            AuditLog(
                actor_user_id=None,
                action="subscription.webhook_failed",
                entity_type="subscription_payment",
                entity_id=payment.id,
                meta={"provider": provider.code, "status": target_status},
            )
        )

    await db.commit()
    return await load_payment(db, payment.id), event.response_payload


async def load_payment_by_provider_id(
    db: AsyncSession,
    *,
    provider_code: str,
    provider_payment_id: str,
) -> SubscriptionPayment:
    payment = await db.scalar(
        select(SubscriptionPayment)
        .options(selectinload(SubscriptionPayment.plan), selectinload(SubscriptionPayment.subscription))
        .where(
            SubscriptionPayment.provider == provider_code,
            SubscriptionPayment.provider_payment_id == provider_payment_id,
        )
    )
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платіж не знайдено.")
    return payment


def validate_webhook_event(payment: SubscriptionPayment, event: PaymentWebhookEvent) -> None:
    if event.subscription_payment_id is not None and event.subscription_payment_id != payment.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook payment id не збігається.")
    if event.amount != payment.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook amount не збігається.")
    if event.currency != payment.currency:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook currency не збігається.")


async def activate_or_extend_subscription(
    db: AsyncSession,
    payment: SubscriptionPayment,
) -> Subscription:
    plan = payment.plan
    if plan is None:
        plan = await db.get(SubscriptionPlan, payment.plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тариф не знайдено.")

    now = datetime.now(UTC)
    await expire_stale_subscriptions(db, payment.seller_id)
    existing = await get_current_subscription_by_seller_id(db, payment.seller_id)
    base_time = now
    if existing is not None and existing.expires_at is not None and existing.expires_at > now:
        base_time = existing.expires_at

    expires_at = base_time + timedelta(days=plan.duration_days)
    if existing is None:
        subscription = Subscription(
            seller_id=payment.seller_id,
            plan_id=plan.id,
            status="active",
            starts_at=now,
            expires_at=expires_at,
        )
        db.add(subscription)
        await db.flush()
        return subscription

    existing.plan_id = plan.id
    existing.status = "active"
    existing.expires_at = expires_at
    await db.flush()
    return existing


async def expire_stale_subscriptions(db: AsyncSession, seller_id: UUID | None = None) -> int:
    now = datetime.now(UTC)
    filters = [
        Subscription.status.in_(("active", "trial")),
        Subscription.expires_at.is_not(None),
        Subscription.expires_at < subscription_visibility_cutoff(now),
    ]
    if seller_id is not None:
        filters.append(Subscription.seller_id == seller_id)

    stale = list(await db.scalars(select(Subscription).where(*filters)))
    for subscription in stale:
        subscription.status = "expired"
    return len(stale)


async def get_active_paid_subscription_by_seller_id(
    db: AsyncSession,
    seller_id: UUID,
) -> Subscription | None:
    now = datetime.now(UTC)
    return await db.scalar(
        select(Subscription)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(
            Subscription.seller_id == seller_id,
            Subscription.status.in_(("active", "trial")),
            SubscriptionPlan.price_amount > 0,
            (Subscription.expires_at.is_(None)) | (Subscription.expires_at >= subscription_visibility_cutoff(now)),
        )
        .order_by(Subscription.expires_at.desc().nullslast(), Subscription.created_at.desc())
        .limit(1)
    )


async def get_current_subscription_by_seller_id(
    db: AsyncSession,
    seller_id: UUID,
) -> Subscription | None:
    now = datetime.now(UTC)
    return await db.scalar(
        select(Subscription)
        .where(
            Subscription.seller_id == seller_id,
            Subscription.status.in_(("active", "trial")),
            (Subscription.expires_at.is_(None)) | (Subscription.expires_at >= subscription_visibility_cutoff(now)),
        )
        .order_by(Subscription.expires_at.desc().nullslast(), Subscription.created_at.desc())
        .limit(1)
    )
