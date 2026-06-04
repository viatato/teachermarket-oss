from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from starlette.responses import JSONResponse

from app.dependencies import DatabaseSession, get_current_user, require_admin
from app.db.models import SubscriptionPayment, SubscriptionPlan, User
from app.modules.subscriptions.schemas import (
    SubscriptionCheckoutCreate,
    SubscriptionPaymentResponse,
    SubscriptionPlanResponse,
)
from app.modules.subscriptions.service import (
    create_subscription_checkout,
    ensure_subscriptions_enabled,
    list_active_plans,
    mark_mock_payment_paid,
    process_payment_webhook,
)
from app.security.rate_limit import rate_limit


router = APIRouter(tags=["subscriptions"], dependencies=[Depends(ensure_subscriptions_enabled)])


def plan_response(plan: SubscriptionPlan) -> SubscriptionPlanResponse:
    return SubscriptionPlanResponse(
        id=plan.id,
        code=plan.code,
        name=plan.name,
        description=plan.description,
        price_amount=plan.price_amount,
        currency=plan.currency,
        duration_days=plan.duration_days,
        product_limit=plan.product_limit,
    )


def payment_response(payment: SubscriptionPayment) -> SubscriptionPaymentResponse:
    return SubscriptionPaymentResponse(
        id=payment.id,
        seller_id=payment.seller_id,
        subscription_id=payment.subscription_id,
        plan_id=payment.plan_id,
        provider=payment.provider,
        provider_payment_id=payment.provider_payment_id,
        payment_url=payment.payment_url,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


@router.get("/subscription-plans", response_model=list[SubscriptionPlanResponse])
async def subscription_plans(db: DatabaseSession) -> list[SubscriptionPlanResponse]:
    plans = await list_active_plans(db)
    return [plan_response(plan) for plan in plans]


@router.post(
    "/seller/subscription/checkout",
    response_model=SubscriptionPaymentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(scope="subscription_checkout", limit=10, window_seconds=60))],
)
async def checkout_subscription(
    payload: SubscriptionCheckoutCreate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SubscriptionPaymentResponse:
    payment = await create_subscription_checkout(db, user=current_user, payload=payload)
    return payment_response(payment)


@router.post(
    "/subscription-payments/mock/{payment_id}/mark-paid",
    response_model=SubscriptionPaymentResponse,
)
async def mark_paid(
    payment_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> SubscriptionPaymentResponse:
    payment = await mark_mock_payment_paid(db, payment_id=payment_id, actor=current_user)
    return payment_response(payment)


@router.post(
    "/subscription-payments/webhook/{provider}",
    dependencies=[Depends(rate_limit(scope="payment_webhook", limit=60, window_seconds=60))],
)
async def payment_webhook(
    provider: str,
    request: Request,
    db: DatabaseSession,
):
    raw_body = await request.body()
    payment, provider_response = await process_payment_webhook(
        db,
        provider_code=provider,
        raw_body=raw_body,
        headers={key.lower(): value for key, value in request.headers.items()},
    )
    if provider_response is not None:
        return JSONResponse(provider_response)
    return payment_response(payment)
