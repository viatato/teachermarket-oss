from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import DatabaseSession, get_current_user
from app.db.models import User
from app.modules.favorites.service import add_favorite, list_favorite_products, remove_favorite
from app.modules.products.router import catalog_item_response
from app.modules.products.schemas import CatalogProductListItem


router = APIRouter(tags=["favorites"])


@router.get("/favorites", response_model=list[CatalogProductListItem])
async def list_favorites(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[CatalogProductListItem]:
    products = await list_favorite_products(db, user=current_user)
    return [catalog_item_response(product) for product in products]


@router.post("/products/{product_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def favorite_product(
    product_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    await add_favorite(db, user=current_user, product_id=product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/products/{product_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def unfavorite_product(
    product_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    await remove_favorite(db, user=current_user, product_id=product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
