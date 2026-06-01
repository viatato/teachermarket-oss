from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SubscriptionPlanResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    price_amount: int
    currency: str
    duration_days: int
    product_limit: int


class SubscriptionCheckoutCreate(BaseModel):
    plan_id: UUID


class SubscriptionPaymentResponse(BaseModel):
    id: UUID
    seller_id: UUID
    subscription_id: UUID | None = None
    plan_id: UUID
    provider: str
    provider_payment_id: str | None = None
    payment_url: str | None = None
    amount: int
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime

