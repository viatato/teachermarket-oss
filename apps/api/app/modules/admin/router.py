from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, select

from app.config import get_settings
from app.dependencies import DatabaseSession, require_admin
from app.db.models import File as FileModel
from app.db.models import Product, SellerProfile, Subscription, User
from app.modules.admin.schemas import (
    AdminActivateSubscriptionRequest,
    AdminBulkProductActionRequest,
    AdminProductsPageResponse,
    AdminProductResponse,
    AdminProductReportResponse,
    AdminProductSellerResponse,
    AdminSellerStatusRequest,
    AdminSubscriptionPlanCreate,
    AdminSubscriptionPlanResponse,
    AdminSubscriptionPlanUpdate,
    AdminSubscriptionResponse,
    AdminSubscriptionSellerResponse,
    AdminUserBlockedRequest,
    ModerationCommentRequest,
)
from app.modules.admin.service import (
    activate_seller_subscription,
    approve_product,
    create_subscription_plan,
    deactivate_subscription_plan,
    get_product_for_moderation,
    hide_product,
    list_admin_products,
    list_admin_subscription_states,
    list_pending_products,
    list_product_reports,
    list_subscription_plans,
    reject_product,
    request_product_changes,
    resolve_product_report,
    restore_product,
    update_seller_status,
    update_subscription_plan,
    update_user_blocked,
)
from app.services.storage import get_storage_adapter
from app.services.storage.s3 import StorageUnavailableError


router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin_subscriptions_enabled() -> None:
    if not get_settings().feature_subscriptions_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Функцію не знайдено.")


def require_admin_reports_enabled() -> None:
    if not get_settings().feature_reports_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Функцію не знайдено.")


def admin_product_response(product: Product) -> AdminProductResponse:
    return AdminProductResponse(
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
        seller=AdminProductSellerResponse(
            id=product.seller.id,
            user_id=product.seller.user_id,
            display_name=product.seller.display_name,
            contact_username=product.seller.contact_username,
            status=product.seller.status,
            user_is_blocked=product.seller.user.is_blocked,
        ),
    )


def admin_subscription_response(
    seller: SellerProfile,
    subscription: Subscription | None,
    product_count: int,
    product_limit: int,
) -> AdminSubscriptionResponse:
    seller_user = seller.__dict__.get("user")
    plan = None
    if subscription is not None and subscription.plan is not None:
        plan = AdminSubscriptionPlanResponse(
            id=subscription.plan.id,
            code=subscription.plan.code,
            name=subscription.plan.name,
            description=subscription.plan.description,
            price_amount=subscription.plan.price_amount,
            currency=subscription.plan.currency,
            product_limit=subscription.plan.product_limit,
            duration_days=subscription.plan.duration_days,
            is_active=subscription.plan.is_active,
        )
    return AdminSubscriptionResponse(
        seller=AdminSubscriptionSellerResponse(
            id=seller.id,
            user_id=seller.user_id,
            display_name=seller.display_name,
            contact_username=seller.contact_username,
            status=seller.status,
            user_is_blocked=seller_user.is_blocked if seller_user else None,
        ),
        subscription_id=subscription.id if subscription else None,
        status=subscription.status if subscription else "none",
        starts_at=subscription.starts_at if subscription else None,
        expires_at=subscription.expires_at if subscription else None,
        plan=plan,
        product_count=product_count,
        product_limit=product_limit,
    )


def admin_plan_response(plan) -> AdminSubscriptionPlanResponse:
    return AdminSubscriptionPlanResponse(
        id=plan.id,
        code=plan.code,
        name=plan.name,
        description=plan.description,
        price_amount=plan.price_amount,
        currency=plan.currency,
        product_limit=plan.product_limit,
        duration_days=plan.duration_days,
        is_active=plan.is_active,
    )


def admin_report_response(report) -> AdminProductReportResponse:
    return AdminProductReportResponse(
        id=report.id,
        product_id=report.product_id,
        product_title=report.product.title,
        reporter_id=report.reporter_id,
        reason=report.reason,
        status=report.status,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get("/products", response_model=AdminProductsPageResponse)
async def read_admin_products(
    db: DatabaseSession,
    _: Annotated[User, Depends(require_admin)],
    product_status: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> AdminProductsPageResponse:
    products, total = await list_admin_products(db, product_status=product_status, page=page, limit=limit)
    return AdminProductsPageResponse(
        items=[admin_product_response(product) for product in products],
        page=page,
        limit=limit,
        total=total,
    )


@router.get("/products/pending", response_model=list[AdminProductResponse])
async def pending_products(
    db: DatabaseSession,
    _: Annotated[User, Depends(require_admin)],
) -> list[AdminProductResponse]:
    products = await list_pending_products(db)
    return [admin_product_response(product) for product in products]


@router.get("/products/{product_id}", response_model=AdminProductResponse)
async def read_admin_product(
    product_id: UUID,
    db: DatabaseSession,
    _: Annotated[User, Depends(require_admin)],
) -> AdminProductResponse:
    product = await get_product_for_moderation(db, product_id)
    return admin_product_response(product)


@router.get("/files/{file_id}")
async def download_admin_file(
    file_id: UUID,
    db: DatabaseSession,
    _: Annotated[User, Depends(require_admin)],
) -> Response:
    file_record = await db.scalar(select(FileModel).where(FileModel.id == file_id))
    if file_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не знайдено.")

    try:
        content = await get_storage_adapter().read(file_record.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл недоступний.") from exc
    except StorageUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Сховище файлів тимчасово недоступне.") from exc

    filename = file_record.original_filename or f"{file_record.id}"
    return Response(
        content=content,
        media_type=file_record.mime_type or "application/octet-stream",
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
        },
    )


@router.post("/products/{product_id}/approve", response_model=AdminProductResponse)
async def approve(
    product_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> AdminProductResponse:
    product = await approve_product(db, actor=current_user, product_id=product_id)
    return admin_product_response(product)


@router.post("/products/{product_id}/reject", response_model=AdminProductResponse)
async def reject(
    product_id: UUID,
    payload: ModerationCommentRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> AdminProductResponse:
    product = await reject_product(db, actor=current_user, product_id=product_id, reason=payload.reason)
    return admin_product_response(product)


@router.post("/products/{product_id}/request-changes", response_model=AdminProductResponse)
async def request_changes(
    product_id: UUID,
    payload: ModerationCommentRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> AdminProductResponse:
    product = await request_product_changes(db, actor=current_user, product_id=product_id, reason=payload.reason)
    return admin_product_response(product)


@router.post("/products/{product_id}/hide", response_model=AdminProductResponse)
async def hide(
    product_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> AdminProductResponse:
    product = await hide_product(db, actor=current_user, product_id=product_id)
    return admin_product_response(product)


@router.post("/products/{product_id}/restore", response_model=AdminProductResponse)
async def restore(
    product_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> AdminProductResponse:
    product = await restore_product(db, actor=current_user, product_id=product_id)
    return admin_product_response(product)


@router.post("/products/bulk-hide", response_model=list[AdminProductResponse])
async def bulk_hide(
    payload: AdminBulkProductActionRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> list[AdminProductResponse]:
    products = []
    for product_id in payload.product_ids:
        products.append(await hide_product(db, actor=current_user, product_id=product_id))
    return [admin_product_response(product) for product in products]


@router.post("/products/bulk-restore", response_model=list[AdminProductResponse])
async def bulk_restore(
    payload: AdminBulkProductActionRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> list[AdminProductResponse]:
    products = []
    for product_id in payload.product_ids:
        products.append(await restore_product(db, actor=current_user, product_id=product_id))
    return [admin_product_response(product) for product in products]


@router.get(
    "/subscriptions",
    response_model=list[AdminSubscriptionResponse],
    dependencies=[Depends(require_admin_subscriptions_enabled)],
)
async def subscriptions(
    db: DatabaseSession,
    _: Annotated[User, Depends(require_admin)],
) -> list[AdminSubscriptionResponse]:
    states = await list_admin_subscription_states(db)
    return [
        admin_subscription_response(seller, subscription, product_count, product_limit)
        for seller, subscription, product_count, product_limit in states
    ]


@router.get(
    "/subscription-plans",
    response_model=list[AdminSubscriptionPlanResponse],
    dependencies=[Depends(require_admin_subscriptions_enabled)],
)
async def admin_subscription_plans(
    db: DatabaseSession,
    _: Annotated[User, Depends(require_admin)],
    include_inactive: bool = True,
) -> list[AdminSubscriptionPlanResponse]:
    plans = await list_subscription_plans(db, include_inactive=include_inactive)
    return [admin_plan_response(plan) for plan in plans]


@router.post(
    "/subscription-plans",
    response_model=AdminSubscriptionPlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_subscriptions_enabled)],
)
async def admin_create_subscription_plan(
    payload: AdminSubscriptionPlanCreate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> AdminSubscriptionPlanResponse:
    plan = await create_subscription_plan(db, actor=current_user, payload=payload)
    return admin_plan_response(plan)


@router.patch(
    "/subscription-plans/{plan_id}",
    response_model=AdminSubscriptionPlanResponse,
    dependencies=[Depends(require_admin_subscriptions_enabled)],
)
async def admin_patch_subscription_plan(
    plan_id: UUID,
    payload: AdminSubscriptionPlanUpdate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> AdminSubscriptionPlanResponse:
    plan = await update_subscription_plan(db, actor=current_user, plan_id=plan_id, payload=payload)
    return admin_plan_response(plan)


@router.delete(
    "/subscription-plans/{plan_id}",
    response_model=AdminSubscriptionPlanResponse,
    dependencies=[Depends(require_admin_subscriptions_enabled)],
)
async def admin_delete_subscription_plan(
    plan_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> AdminSubscriptionPlanResponse:
    plan = await deactivate_subscription_plan(db, actor=current_user, plan_id=plan_id)
    return admin_plan_response(plan)


@router.post(
    "/sellers/{seller_id}/activate-subscription",
    response_model=AdminSubscriptionResponse,
    dependencies=[Depends(require_admin_subscriptions_enabled)],
)
async def activate_subscription(
    seller_id: UUID,
    payload: AdminActivateSubscriptionRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> AdminSubscriptionResponse:
    subscription = await activate_seller_subscription(
        db,
        actor=current_user,
        seller_id=seller_id,
        plan_id=payload.plan_id,
        duration_days=payload.duration_days,
    )
    seller = subscription.seller
    product_count = await db.scalar(
        select(func.count(Product.id)).where(
            Product.seller_id == seller.id,
            Product.status.in_(("published", "pending_moderation")),
        )
    )
    return admin_subscription_response(
        seller,
        subscription,
        product_count or 0,
        subscription.plan.product_limit if subscription.plan else 0,
    )


@router.patch("/sellers/{seller_id}/status", response_model=AdminSubscriptionSellerResponse)
async def patch_seller_status(
    seller_id: UUID,
    payload: AdminSellerStatusRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> AdminSubscriptionSellerResponse:
    seller = await update_seller_status(db, actor=current_user, seller_id=seller_id, new_status=payload.status)
    seller_user = seller.__dict__.get("user")
    return AdminSubscriptionSellerResponse(
        id=seller.id,
        user_id=seller.user_id,
        display_name=seller.display_name,
        contact_username=seller.contact_username,
        status=seller.status,
        user_is_blocked=seller_user.is_blocked if seller_user else None,
    )


@router.patch("/users/{user_id}/blocked")
async def patch_user_blocked(
    user_id: UUID,
    payload: AdminUserBlockedRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> dict[str, object]:
    user = await update_user_blocked(db, actor=current_user, user_id=user_id, is_blocked=payload.is_blocked)
    return {"id": user.id, "telegram_id": user.telegram_id, "is_blocked": user.is_blocked}


@router.get(
    "/reports",
    response_model=list[AdminProductReportResponse],
    dependencies=[Depends(require_admin_reports_enabled)],
)
async def admin_reports(
    db: DatabaseSession,
    _: Annotated[User, Depends(require_admin)],
    report_status: str | None = Query(default=None, alias="status"),
) -> list[AdminProductReportResponse]:
    reports = await list_product_reports(db, report_status=report_status)
    return [admin_report_response(report) for report in reports]


@router.post(
    "/reports/{report_id}/resolve",
    response_model=AdminProductReportResponse,
    dependencies=[Depends(require_admin_reports_enabled)],
)
async def admin_resolve_report(
    report_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(require_admin)],
) -> AdminProductReportResponse:
    report = await resolve_product_report(db, actor=current_user, report_id=report_id)
    return admin_report_response(report)
