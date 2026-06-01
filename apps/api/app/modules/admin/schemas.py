from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ModerationCommentRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


class AdminProductSellerResponse(BaseModel):
    id: UUID
    user_id: UUID
    display_name: str
    contact_username: str | None = None
    status: str
    user_is_blocked: bool


class AdminProductResponse(BaseModel):
    id: UUID
    seller_id: UUID
    title: str
    description: str
    language: str
    level: str | None = None
    category: str
    audience: str | None = None
    price_amount: int
    currency: str
    product_file_id: UUID | None = None
    delivery_method: str
    external_file_url: str | None = None
    preview_file_ids: list[UUID]
    status: str
    rejection_reason: str | None = None
    seller: AdminProductSellerResponse


class AdminSubscriptionSellerResponse(BaseModel):
    id: UUID
    user_id: UUID
    display_name: str
    contact_username: str | None = None
    status: str | None = None
    user_is_blocked: bool | None = None


class AdminSubscriptionPlanResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    price_amount: int
    currency: str
    product_limit: int
    duration_days: int
    is_active: bool = True


class AdminSubscriptionResponse(BaseModel):
    seller: AdminSubscriptionSellerResponse
    subscription_id: UUID | None = None
    status: str
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    plan: AdminSubscriptionPlanResponse | None = None
    product_count: int
    product_limit: int


class AdminActivateSubscriptionRequest(BaseModel):
    plan_id: UUID
    duration_days: int | None = Field(default=None, ge=1, le=3660)


class AdminProductsPageResponse(BaseModel):
    items: list[AdminProductResponse]
    page: int
    limit: int
    total: int


class AdminSubscriptionPlanCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    price_amount: int = Field(ge=0)
    currency: str = Field(default="UAH", min_length=3, max_length=3)
    duration_days: int = Field(ge=1, le=3660)
    product_limit: int = Field(ge=0, le=10000)
    is_active: bool = True


class AdminSubscriptionPlanUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=64)
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    price_amount: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    duration_days: int | None = Field(default=None, ge=1, le=3660)
    product_limit: int | None = Field(default=None, ge=0, le=10000)
    is_active: bool | None = None


class AdminSellerStatusRequest(BaseModel):
    status: str = Field(pattern="^(active|suspended)$")


class AdminUserBlockedRequest(BaseModel):
    is_blocked: bool


class AdminBulkProductActionRequest(BaseModel):
    product_ids: list[UUID] = Field(min_length=1, max_length=100)


class AdminProductReportResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_title: str
    reporter_id: UUID
    reason: str
    status: str
    created_at: datetime
    updated_at: datetime
