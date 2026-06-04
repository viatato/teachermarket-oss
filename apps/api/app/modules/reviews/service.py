from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AuditLog, Product, Review, SellerProfile, User
from app.modules.products.service import cleanup_catalog_subscriptions, visible_product_condition
from app.modules.reviews.schemas import ReviewCreate, ReviewUpdate


async def load_reviewable_product(db: AsyncSession, product_id: UUID) -> Product:
    await cleanup_catalog_subscriptions(db)
    product = await db.scalar(
        select(Product)
        .options(selectinload(Product.seller).selectinload(SellerProfile.user))
        .where(Product.id == product_id, Product.status == "published", visible_product_condition(datetime.now(UTC)))
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матеріал не знайдено.")
    return product


async def list_product_reviews(db: AsyncSession, product_id: UUID) -> tuple[list[Review], float | None, int]:
    await load_reviewable_product(db, product_id)
    reviews = list(
        await db.scalars(
            select(Review)
            .options(selectinload(Review.buyer))
            .where(Review.product_id == product_id)
            .order_by(Review.created_at.desc())
        )
    )
    average = await db.scalar(select(func.avg(Review.rating)).where(Review.product_id == product_id))
    return reviews, float(average) if average is not None else None, len(reviews)


async def create_review(db: AsyncSession, *, user: User, product_id: UUID, payload: ReviewCreate) -> Review:
    product = await load_reviewable_product(db, product_id)
    if product.seller.user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не можна оцінювати власний матеріал.")
    existing = await db.scalar(select(Review).where(Review.product_id == product_id, Review.buyer_id == user.id))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ви вже залишили відгук.")
    review = Review(product_id=product_id, buyer_id=user.id, rating=payload.rating, text=(payload.text or "").strip() or None)
    db.add(review)
    await db.flush()
    db.add(AuditLog(actor_user_id=user.id, action="review.created", entity_type="review", entity_id=review.id))
    await db.commit()
    return await load_review(db, review.id, user=user)


async def load_review(db: AsyncSession, review_id: UUID, *, user: User | None = None) -> Review:
    filters = [Review.id == review_id]
    if user is not None:
        filters.append(Review.buyer_id == user.id)
    review = await db.scalar(select(Review).options(selectinload(Review.buyer)).where(*filters))
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Відгук не знайдено.")
    return review


async def update_review(db: AsyncSession, *, user: User, review_id: UUID, payload: ReviewUpdate) -> Review:
    review = await load_review(db, review_id, user=user)
    if payload.rating is not None:
        review.rating = payload.rating
    if payload.text is not None:
        review.text = payload.text.strip() or None
    db.add(AuditLog(actor_user_id=user.id, action="review.updated", entity_type="review", entity_id=review.id))
    await db.commit()
    return await load_review(db, review.id, user=user)


async def delete_review(db: AsyncSession, *, user: User, review_id: UUID) -> None:
    review = await load_review(db, review_id, user=user)
    db.add(AuditLog(actor_user_id=user.id, action="review.deleted", entity_type="review", entity_id=review.id))
    await db.delete(review)
    await db.commit()
