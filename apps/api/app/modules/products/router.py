from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.config import get_settings
from app.dependencies import DatabaseSession, get_current_user, get_optional_user
from app.db.models import Product, User
from app.modules.products.schemas import (
    CatalogProductDetail,
    CatalogProductListItem,
    CatalogProductsResponse,
    CatalogSellerResponse,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ProductViewResponse,
)
from app.modules.products.service import (
    create_product,
    delete_product,
    get_published_product,
    list_published_products,
    submit_product,
    track_product_view,
    update_product,
)


router = APIRouter(prefix="/products", tags=["products"])


def preview_url(file_id: UUID | None) -> str | None:
    if file_id is None:
        return None
    return f"{get_settings().api_base_url.rstrip('/')}/files/preview/{file_id}"


def product_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        seller_id=product.seller_id,
        title=product.title,
        description=product.description,
        language=product.language,
        level=product.level,
        category=product.category,
        audience=product.audience,
        price_amount=product.price_amount,
        currency=product.currency,
        product_file_id=product.product_file_id,
        delivery_method=product.delivery_method,
        external_file_url=product.external_file_url,
        preview_file_ids=[preview.file_id for preview in sorted(product.previews, key=lambda item: item.sort_order)],
        status=product.status,
        rejection_reason=product.rejection_reason,
    )


def catalog_seller_response(product: Product) -> CatalogSellerResponse:
    return CatalogSellerResponse(
        id=product.seller.id,
        display_name=product.seller.display_name,
        bio=product.seller.bio,
        contact_username=product.seller.contact_username,
    )


def catalog_item_response(product: Product) -> CatalogProductListItem:
    previews = sorted(product.previews, key=lambda item: item.sort_order)
    return CatalogProductListItem(
        id=product.id,
        title=product.title,
        language=product.language,
        level=product.level,
        category=product.category,
        audience=product.audience,
        price_amount=product.price_amount,
        currency=product.currency,
        preview_file_id=previews[0].file_id if previews else None,
        preview_url=preview_url(previews[0].file_id if previews else None),
        delivery_method=product.delivery_method,
        created_at=product.created_at,
        published_at=product.published_at,
        seller=catalog_seller_response(product),
    )


def catalog_detail_response(product: Product) -> CatalogProductDetail:
    previews = sorted(product.previews, key=lambda item: item.sort_order)
    preview_urls = [url for url in (preview_url(preview.file_id) for preview in previews) if url]
    return CatalogProductDetail(
        id=product.id,
        title=product.title,
        description=product.description,
        language=product.language,
        level=product.level,
        category=product.category,
        audience=product.audience,
        price_amount=product.price_amount,
        currency=product.currency,
        preview_file_ids=[preview.file_id for preview in previews],
        preview_urls=preview_urls,
        delivery_method=product.delivery_method,
        created_at=product.created_at,
        published_at=product.published_at,
        seller=catalog_seller_response(product),
    )


@router.get("", response_model=CatalogProductsResponse)
async def catalog(
    db: DatabaseSession,
    language: str | None = None,
    level: str | None = None,
    category: str | None = None,
    audience: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    search: str | None = None,
    sort: str = "new",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> CatalogProductsResponse:
    products, total = await list_published_products(
        db,
        language=language,
        level=level,
        category=category,
        audience=audience,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort=sort,
        page=page,
        limit=limit,
    )
    return CatalogProductsResponse(
        items=[catalog_item_response(product) for product in products],
        page=page,
        limit=limit,
        total=total,
    )


@router.get("/{product_id}", response_model=CatalogProductDetail)
async def detail(product_id: UUID, db: DatabaseSession) -> CatalogProductDetail:
    product = await get_published_product(db, product_id)
    return catalog_detail_response(product)


@router.post("/{product_id}/view", response_model=ProductViewResponse)
async def view_product(
    product_id: UUID,
    request: Request,
    db: DatabaseSession,
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> ProductViewResponse:
    tracked = await track_product_view(
        db,
        product_id=product_id,
        viewer=current_user,
        client_host=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return ProductViewResponse(tracked=tracked)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: ProductCreate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProductResponse:
    product = await create_product(db, current_user, payload)
    return product_response(product)


@router.patch("/{product_id}", response_model=ProductResponse)
async def patch(
    product_id: UUID,
    payload: ProductUpdate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProductResponse:
    product = await update_product(db, current_user, product_id, payload)
    return product_response(product)


@router.post("/{product_id}/submit", response_model=ProductResponse)
async def submit(
    product_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProductResponse:
    product = await submit_product(db, current_user, product_id)
    return product_response(product)


@router.delete("/{product_id}", response_model=ProductResponse)
async def delete(
    product_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProductResponse:
    product = await delete_product(db, current_user, product_id)
    return product_response(product)
