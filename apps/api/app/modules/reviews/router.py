from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.config import get_settings
from app.dependencies import DatabaseSession, get_current_user
from app.db.models import Review, User
from app.modules.reviews.schemas import ProductReviewsResponse, ReviewCreate, ReviewResponse, ReviewUpdate
from app.modules.reviews.service import create_review, delete_review, list_product_reviews, update_review


def require_reviews_enabled() -> None:
    if not get_settings().feature_reviews_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Функцію не знайдено.")


router = APIRouter(tags=["reviews"], dependencies=[Depends(require_reviews_enabled)])


def buyer_display_name(review: Review) -> str | None:
    if review.buyer.username:
        return f"@{review.buyer.username}"
    return " ".join(part for part in (review.buyer.first_name, review.buyer.last_name) if part) or None


def review_response(review: Review) -> ReviewResponse:
    return ReviewResponse(
        id=review.id,
        product_id=review.product_id,
        buyer_id=review.buyer_id,
        buyer_display_name=buyer_display_name(review),
        rating=review.rating,
        text=review.text,
        created_at=review.created_at,
    )


@router.get("/products/{product_id}/reviews", response_model=ProductReviewsResponse)
async def product_reviews(product_id: UUID, db: DatabaseSession) -> ProductReviewsResponse:
    reviews, average, total = await list_product_reviews(db, product_id)
    return ProductReviewsResponse(items=[review_response(review) for review in reviews], average_rating=average, total=total)


@router.post("/products/{product_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def post_review(
    product_id: UUID,
    payload: ReviewCreate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReviewResponse:
    review = await create_review(db, user=current_user, product_id=product_id, payload=payload)
    return review_response(review)


@router.patch("/reviews/{review_id}", response_model=ReviewResponse)
async def patch_review(
    review_id: UUID,
    payload: ReviewUpdate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReviewResponse:
    review = await update_review(db, user=current_user, review_id=review_id, payload=payload)
    return review_response(review)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_review(
    review_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    await delete_review(db, user=current_user, review_id=review_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
