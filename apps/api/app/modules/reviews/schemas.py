from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)


class ReviewResponse(BaseModel):
    id: UUID
    product_id: UUID
    buyer_id: UUID
    buyer_display_name: str | None = None
    rating: int
    text: str | None = None
    created_at: datetime


class ProductReviewsResponse(BaseModel):
    items: list[ReviewResponse]
    average_rating: float | None = None
    total: int
