import hashlib
from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.config import get_settings
from app.db.models import (
    AuditLog,
    File,
    OneTimePlacement,
    Product,
    ProductPreview,
    ProductViewEvent,
    SellerProfile,
    Subscription,
    SubscriptionPlan,
    User,
)
from app.modules.files.service import PREVIEW_IMAGE_KIND, PRODUCT_FILE_KIND
from app.modules.products.schemas import DELIVERY_UPLOADED_FILE, ProductCreate, ProductUpdate
from app.modules.sellers.service import get_seller_profile
from app.modules.subscriptions.service import expire_stale_subscriptions, subscription_visibility_cutoff


COUNTED_PRODUCT_STATUSES = {"published", "pending_moderation"}
FREE_VISIBLE_PRODUCT_LIMIT = 3


def is_product_visible_by_policy(
    *,
    has_paid_subscription: bool,
    has_one_time_placement: bool,
    seller_published_rank: int | None,
) -> bool:
    return has_paid_subscription or has_one_time_placement or (
        seller_published_rank is not None and seller_published_rank <= FREE_VISIBLE_PRODUCT_LIMIT
    )


async def cleanup_catalog_subscriptions(db: AsyncSession) -> None:
    if not get_settings().feature_subscriptions_enabled:
        return
    expired_count = await expire_stale_subscriptions(db)
    if expired_count:
        await db.commit()


def paid_subscription_visibility_condition(now: datetime):
    cutoff = subscription_visibility_cutoff(now)
    return (
        select(Subscription.id)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(
            Subscription.seller_id == Product.seller_id,
            Subscription.status.in_(("active", "trial")),
            SubscriptionPlan.price_amount > 0,
            (Subscription.expires_at.is_(None)) | (Subscription.expires_at >= cutoff),
        )
        .correlate(Product)
        .exists()
    )


def active_placement_visibility_condition():
    return (
        select(OneTimePlacement.id)
        .where(
            OneTimePlacement.product_id == Product.id,
            OneTimePlacement.status == "active",
        )
        .correlate(Product)
        .exists()
    )


def free_tier_visibility_condition():
    free_product = aliased(Product)
    free_rank = (
        select(func.count(free_product.id))
        .where(
            free_product.seller_id == Product.seller_id,
            free_product.status == "published",
            or_(
                free_product.created_at < Product.created_at,
                and_(free_product.created_at == Product.created_at, free_product.id <= Product.id),
            ),
        )
        .correlate(Product)
        .scalar_subquery()
    )
    return free_rank <= FREE_VISIBLE_PRODUCT_LIMIT


def visible_product_condition(now: datetime):
    settings = get_settings()
    conditions = [free_tier_visibility_condition()]
    if settings.feature_subscriptions_enabled:
        conditions.append(paid_subscription_visibility_condition(now))
    if settings.feature_placements_enabled:
        conditions.append(active_placement_visibility_condition())
    return or_(*conditions)


async def load_product_with_previews(db: AsyncSession, product_id: UUID) -> Product:
    product = await db.scalar(
        select(Product)
        .options(selectinload(Product.previews))
        .where(Product.id == product_id)
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матеріал не знайдено.")
    return product


async def require_seller_profile(db: AsyncSession, user: User) -> SellerProfile:
    profile = await get_seller_profile(db, user)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Спочатку створіть профіль автора.",
        )
    return profile


async def get_active_product_limit(db: AsyncSession, seller: SellerProfile) -> int:
    settings = get_settings()
    if not settings.feature_subscriptions_enabled:
        return settings.default_free_product_limit
    now = datetime.now(UTC)
    result = await db.execute(
        select(SubscriptionPlan.product_limit)
        .join(Subscription, Subscription.plan_id == SubscriptionPlan.id)
        .where(
            Subscription.seller_id == seller.id,
            Subscription.status.in_(("active", "trial")),
            (Subscription.expires_at.is_(None)) | (Subscription.expires_at >= subscription_visibility_cutoff(now)),
            SubscriptionPlan.is_active.is_(True),
        )
        .order_by(SubscriptionPlan.product_limit.desc())
        .limit(1)
    )
    product_limit = result.scalar_one_or_none()
    if product_limit is not None:
        return product_limit
    return get_settings().default_free_product_limit


async def enforce_product_limit(db: AsyncSession, seller: SellerProfile) -> None:
    product_limit = await get_active_product_limit(db, seller)
    count = await db.scalar(
        select(func.count(Product.id)).where(
            Product.seller_id == seller.id,
            Product.status.in_(COUNTED_PRODUCT_STATUSES),
        )
    )
    if (count or 0) >= product_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Досягнуто ліміт матеріалів для вашого тарифу.",
        )


async def validate_owned_file(
    db: AsyncSession,
    *,
    owner: User,
    file_id: UUID,
    expected_kind: str,
) -> File:
    file = await db.scalar(
        select(File).where(
            File.id == file_id,
            File.owner_id == owner.id,
            File.file_kind == expected_kind,
        )
    )
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл не знайдено або він має неправильний тип.",
        )
    return file


async def validate_product_files(
    db: AsyncSession,
    *,
    owner: User,
    product_file_id: UUID | None,
    delivery_method: str,
    preview_file_ids: list[UUID],
) -> None:
    if delivery_method == DELIVERY_UPLOADED_FILE and product_file_id is not None:
        await validate_owned_file(db, owner=owner, file_id=product_file_id, expected_kind=PRODUCT_FILE_KIND)
    unique_preview_ids = set(preview_file_ids)
    if len(unique_preview_ids) != len(preview_file_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Превʼю не мають повторюватися.",
        )
    for preview_file_id in preview_file_ids:
        await validate_owned_file(db, owner=owner, file_id=preview_file_id, expected_kind=PREVIEW_IMAGE_KIND)


async def create_product(db: AsyncSession, user: User, payload: ProductCreate) -> Product:
    seller = await require_seller_profile(db, user)
    await enforce_product_limit(db, seller)
    await validate_product_files(
        db,
        owner=user,
        product_file_id=payload.product_file_id,
        delivery_method=payload.delivery_method,
        preview_file_ids=payload.preview_file_ids,
    )

    product = Product(
        seller_id=seller.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        language=payload.language,
        level=payload.level,
        category=payload.category,
        audience=payload.audience,
        price_amount=payload.price_amount,
        currency=payload.currency.upper(),
        product_file_id=payload.product_file_id,
        delivery_method=payload.delivery_method,
        external_file_url=payload.external_file_url,
        status="draft",
    )
    db.add(product)
    await db.flush()
    for index, preview_file_id in enumerate(payload.preview_file_ids):
        db.add(ProductPreview(product_id=product.id, file_id=preview_file_id, sort_order=index))
    db.add(
        AuditLog(
            actor_user_id=user.id,
            action="product.created",
            entity_type="product",
            entity_id=product.id,
        )
    )
    await db.commit()
    return await load_product_with_previews(db, product.id)


async def get_owned_product(db: AsyncSession, user: User, product_id: UUID) -> Product:
    seller = await require_seller_profile(db, user)
    product = await db.scalar(
        select(Product)
        .options(selectinload(Product.previews))
        .where(Product.id == product_id, Product.seller_id == seller.id)
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матеріал не знайдено.")
    return product


async def update_product(db: AsyncSession, user: User, product_id: UUID, payload: ProductUpdate) -> Product:
    product = await get_owned_product(db, user, product_id)
    if product.status not in {"draft", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Можна редагувати лише чернетку або відхилений матеріал.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    preview_file_ids = update_data.pop("preview_file_ids", None)
    product_file_id = update_data.get("product_file_id")
    delivery_method = update_data.get("delivery_method", product.delivery_method)
    external_file_url = update_data.get("external_file_url", product.external_file_url)
    if product_file_id is not None:
        await validate_owned_file(db, owner=user, file_id=product_file_id, expected_kind=PRODUCT_FILE_KIND)
    if delivery_method == DELIVERY_UPLOADED_FILE and product_file_id is None and product.product_file_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для завантаженого файлу потрібен product_file_id.",
        )
    if delivery_method == "external_link" and not external_file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для посилання потрібно вказати URL.",
        )
    if "delivery_method" in update_data and delivery_method != "external_link":
        update_data["external_file_url"] = None
    if preview_file_ids is not None:
        for preview_file_id in preview_file_ids:
            await validate_owned_file(db, owner=user, file_id=preview_file_id, expected_kind=PREVIEW_IMAGE_KIND)
        product.previews.clear()
        await db.flush()
        for index, preview_file_id in enumerate(preview_file_ids):
            db.add(ProductPreview(product_id=product.id, file_id=preview_file_id, sort_order=index))

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        if field == "currency" and value:
            value = value.upper()
        setattr(product, field, value)

    db.add(
        AuditLog(
            actor_user_id=user.id,
            action="product.updated",
            entity_type="product",
            entity_id=product.id,
            meta={"fields": sorted(update_data.keys())},
        )
    )
    await db.commit()
    return await load_product_with_previews(db, product.id)


async def submit_product(db: AsyncSession, user: User, product_id: UUID) -> Product:
    seller = await require_seller_profile(db, user)
    product = await get_owned_product(db, user, product_id)
    if product.status not in {"draft", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Матеріал вже відправлено або опубліковано.",
        )
    await enforce_product_limit(db, seller)
    product.status = "pending_moderation"
    product.rejection_reason = None
    db.add(
        AuditLog(
            actor_user_id=user.id,
            action="product.submitted",
            entity_type="product",
            entity_id=product.id,
        )
    )
    await db.commit()
    return await load_product_with_previews(db, product.id)


async def delete_product(db: AsyncSession, user: User, product_id: UUID) -> Product:
    product = await get_owned_product(db, user, product_id)
    if product.status == "deleted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Матеріал вже видалено.")
    product.status = "deleted"
    db.add(
        AuditLog(
            actor_user_id=user.id,
            action="product.deleted",
            entity_type="product",
            entity_id=product.id,
        )
    )
    await db.commit()
    return await load_product_with_previews(db, product.id)


async def list_published_products(
    db: AsyncSession,
    *,
    language: str | None = None,
    level: str | None = None,
    category: str | None = None,
    audience: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    search: str | None = None,
    sort: str = "new",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Product], int]:
    await cleanup_catalog_subscriptions(db)
    now = datetime.now(UTC)
    filters = [Product.status == "published"]
    filters.append(visible_product_condition(now))
    if language:
        filters.append(Product.language == language)
    if level:
        filters.append(Product.level == level)
    if category:
        filters.append(Product.category == category)
    if audience:
        filters.append(Product.audience == audience)
    if min_price is not None:
        filters.append(Product.price_amount >= min_price)
    if max_price is not None:
        filters.append(Product.price_amount <= max_price)
    if search:
        pattern = f"%{search}%"
        filters.append(or_(Product.title.ilike(pattern), Product.description.ilike(pattern)))

    total = await db.scalar(select(func.count(Product.id)).where(*filters))
    query = (
        select(Product)
        .options(selectinload(Product.previews), selectinload(Product.seller))
        .where(*filters)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    if sort == "cheap":
        query = query.order_by(Product.price_amount.asc(), Product.published_at.desc())
    elif sort == "expensive":
        query = query.order_by(Product.price_amount.desc(), Product.published_at.desc())
    else:
        query = query.order_by(Product.published_at.desc().nullslast(), Product.created_at.desc())

    products = list(await db.scalars(query))
    return products, total or 0


async def get_published_product(db: AsyncSession, product_id: UUID) -> Product:
    await cleanup_catalog_subscriptions(db)
    now = datetime.now(UTC)
    product = await db.scalar(
        select(Product)
        .options(selectinload(Product.previews), selectinload(Product.seller))
        .where(Product.id == product_id, Product.status == "published", visible_product_condition(now))
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матеріал не знайдено.")
    return product


def anonymous_view_key(*, client_host: str | None, user_agent: str | None) -> str:
    raw = f"{client_host or 'unknown'}:{user_agent or 'unknown'}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def track_product_view(
    db: AsyncSession,
    *,
    product_id: UUID,
    viewer: User | None,
    client_host: str | None,
    user_agent: str | None,
    today: date | None = None,
) -> bool:
    product = await db.scalar(
        select(Product)
        .options(selectinload(Product.seller))
        .where(Product.id == product_id, Product.status == "published", visible_product_condition(datetime.now(UTC)))
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матеріал не знайдено.")
    if viewer is not None and product.seller.user_id == viewer.id:
        return False

    view_day = today or datetime.now(UTC).date()
    filters = [ProductViewEvent.product_id == product.id, ProductViewEvent.view_day == view_day]
    anonymous_key = None
    if viewer is not None:
        filters.append(ProductViewEvent.viewer_user_id == viewer.id)
    else:
        anonymous_key = anonymous_view_key(client_host=client_host, user_agent=user_agent)
        filters.append(ProductViewEvent.viewer_user_id.is_(None))
        filters.append(ProductViewEvent.anonymous_key == anonymous_key)

    existing = await db.scalar(select(ProductViewEvent.id).where(*filters).limit(1))
    if existing is not None:
        return False

    db.add(
        ProductViewEvent(
            product_id=product.id,
            viewer_user_id=viewer.id if viewer else None,
            anonymous_key=anonymous_key,
            view_day=view_day,
        )
    )
    await db.commit()
    return True
