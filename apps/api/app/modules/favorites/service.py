from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Favorite, Product, User
from app.modules.products.service import cleanup_catalog_subscriptions, visible_product_condition


async def get_published_product_or_404(db: AsyncSession, product_id: UUID) -> Product:
    await cleanup_catalog_subscriptions(db)
    product = await db.scalar(
        select(Product).where(Product.id == product_id, Product.status == "published", visible_product_condition(datetime.now(UTC)))
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матеріал не знайдено.")
    return product


async def add_favorite(db: AsyncSession, *, user: User, product_id: UUID) -> Favorite:
    await get_published_product_or_404(db, product_id)
    favorite = await db.scalar(select(Favorite).where(Favorite.user_id == user.id, Favorite.product_id == product_id))
    if favorite is not None:
        return favorite

    favorite = Favorite(user_id=user.id, product_id=product_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite


async def remove_favorite(db: AsyncSession, *, user: User, product_id: UUID) -> None:
    favorite = await db.scalar(select(Favorite).where(Favorite.user_id == user.id, Favorite.product_id == product_id))
    if favorite is None:
        return
    await db.delete(favorite)
    await db.commit()


async def list_favorite_products(db: AsyncSession, *, user: User) -> list[Product]:
    await cleanup_catalog_subscriptions(db)
    result = await db.scalars(
        select(Product)
        .join(Favorite, Favorite.product_id == Product.id)
        .options(selectinload(Product.previews), selectinload(Product.seller))
        .where(Favorite.user_id == user.id, Product.status == "published", visible_product_condition(datetime.now(UTC)))
        .order_by(Favorite.created_at.desc())
    )
    return list(result)


async def favorite_product_ids(db: AsyncSession, *, user: User, product_ids: list[UUID]) -> set[UUID]:
    if not product_ids:
        return set()
    result = await db.scalars(
        select(Favorite.product_id).where(Favorite.user_id == user.id, Favorite.product_id.in_(product_ids))
    )
    return set(result)
