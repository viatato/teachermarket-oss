from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SellerProfileCreate(BaseModel):
    display_name: str = Field(min_length=2, max_length=255)
    bio: str | None = Field(default=None, max_length=2000)
    contact_username: str | None = Field(default=None, max_length=255)

    @field_validator("contact_username")
    @classmethod
    def clean_contact_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().removeprefix("@")
        return value or None


class SellerProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=255)
    bio: str | None = Field(default=None, max_length=2000)
    contact_username: str | None = Field(default=None, max_length=255)

    @field_validator("contact_username")
    @classmethod
    def clean_contact_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().removeprefix("@")
        return value or None


class SellerProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    display_name: str
    bio: str | None = None
    contact_username: str | None = None
    contact_url: str | None = None
    status: str


class SellerProductResponse(BaseModel):
    id: UUID
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
    status: str
    rejection_reason: str | None = None
    preview_file_ids: list[UUID]
    preview_urls: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None


class SellerProductVisibilityResponse(BaseModel):
    product_id: UUID
    is_visible: bool
    primary_reason: str
    reasons: list[str]
    product_status: str
    published_rank: int | None = None
    free_tier_limit: int
    has_paid_subscription_visibility: bool
    subscription_status: str | None = None
    subscription_expires_at: datetime | None = None
    subscription_grace_until: datetime | None = None
    has_active_placement: bool
    active_placement_id: UUID | None = None
    placement_checkout_available: bool


class SellerContactRequestResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_title: str
    requester_telegram_id: int | None = None
    requester_username: str | None = None
    requester_display_name: str | None = None
    message: str | None = None
    status: str = "new"
    created_at: datetime


class SellerContactRequestUpdate(BaseModel):
    status: str = Field(pattern="^(new|handled|archived)$")


class SellerSubscriptionPlanResponse(BaseModel):
    id: UUID
    code: str
    name: str
    price_amount: int
    currency: str
    duration_days: int
    product_limit: int


class SellerSubscriptionResponse(BaseModel):
    subscription_id: UUID | None = None
    status: str
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    plan: SellerSubscriptionPlanResponse | None = None
    product_limit: int
    product_count: int
    can_add_product: bool


class SellerPlacementPurchaseResponse(BaseModel):
    ok: bool
    placement_id: UUID
    product_id: UUID
    paid_amount: int


class SellerPlacementResponse(BaseModel):
    placement_id: UUID
    product_id: UUID
    product_title: str | None = None
    paid_amount: int
    currency: str
    paid_at: datetime
    status: str
    created_at: datetime


class SellerPlacementsResponse(BaseModel):
    items: list[SellerPlacementResponse]
    page: int
    limit: int
    total: int


class SellerStatsResponse(BaseModel):
    products_by_status: dict[str, int]
    contacts_total: int
    contacts_new: int
    reviews_total: int
    average_rating: float | None = None
    views_total: int
    views_7d: int
