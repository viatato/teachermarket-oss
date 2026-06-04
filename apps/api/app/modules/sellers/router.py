from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import get_settings
from app.dependencies import DatabaseSession, get_current_user
from app.db.models import ContactRequest, OneTimePlacement, Product, SellerProfile, Subscription, User
from app.modules.sellers.schemas import (
    SellerContactRequestResponse,
    SellerPlacementPurchaseResponse,
    SellerPlacementResponse,
    SellerPlacementsResponse,
    SellerProductResponse,
    SellerProductVisibilityResponse,
    SellerProfileCreate,
    SellerProfileResponse,
    SellerProfileUpdate,
    SellerStatsResponse,
    SellerContactRequestUpdate,
    SellerSubscriptionPlanResponse,
    SellerSubscriptionResponse,
)
from app.modules.sellers.service import (
    buy_one_time_placement,
    create_seller_profile,
    get_seller_profile,
    get_seller_product_visibility,
    get_seller_stats,
    get_seller_subscription_state,
    list_seller_contact_requests,
    list_seller_placements,
    list_seller_products,
    update_seller_contact_request,
    update_seller_profile,
)


router = APIRouter(prefix="/seller", tags=["seller"])


def seller_response(profile: SellerProfile) -> SellerProfileResponse:
    return SellerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        contact_username=profile.contact_username,
        contact_url=profile.contact_url,
        status=profile.status,
    )


def seller_product_response(product: Product) -> SellerProductResponse:
    previews = sorted(product.previews, key=lambda item: item.sort_order)
    base_url = get_settings().api_base_url.rstrip("/")
    return SellerProductResponse(
        id=product.id,
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
        status=product.status,
        rejection_reason=product.rejection_reason,
        preview_file_ids=[preview.file_id for preview in previews],
        preview_urls=[f"{base_url}/files/preview/{preview.file_id}" for preview in previews],
        created_at=product.created_at,
        updated_at=product.updated_at,
        published_at=product.published_at,
    )


def placement_amount_major(placement: OneTimePlacement) -> int:
    return placement.paid_amount // 100


def seller_placement_response(placement: OneTimePlacement) -> SellerPlacementResponse:
    return SellerPlacementResponse(
        placement_id=placement.id,
        product_id=placement.product_id,
        product_title=placement.product.title if placement.product else None,
        paid_amount=placement_amount_major(placement),
        currency=placement.currency,
        paid_at=placement.paid_at,
        status=placement.status,
        created_at=placement.created_at,
    )


def requester_display_name(contact_request: ContactRequest) -> str | None:
    requester = contact_request.requester
    if requester is None:
        return contact_request.requester_username
    if requester.username:
        return f"@{requester.username}"
    full_name = " ".join(part for part in (requester.first_name, requester.last_name) if part)
    return full_name or None


def seller_contact_request_response(contact_request: ContactRequest) -> SellerContactRequestResponse:
    return SellerContactRequestResponse(
        id=contact_request.id,
        product_id=contact_request.product_id,
        product_title=contact_request.product.title,
        requester_telegram_id=contact_request.requester_telegram_id,
        requester_username=contact_request.requester_username,
        requester_display_name=requester_display_name(contact_request),
        message=contact_request.message,
        status=contact_request.status,
        created_at=contact_request.created_at,
    )


def seller_subscription_response(
    subscription: Subscription | None,
    product_count: int,
    product_limit: int,
) -> SellerSubscriptionResponse:
    plan = None
    if subscription is not None and subscription.plan is not None:
        plan = SellerSubscriptionPlanResponse(
            id=subscription.plan.id,
            code=subscription.plan.code,
            name=subscription.plan.name,
            price_amount=subscription.plan.price_amount,
            currency=subscription.plan.currency,
            duration_days=subscription.plan.duration_days,
            product_limit=subscription.plan.product_limit,
        )
    return SellerSubscriptionResponse(
        subscription_id=subscription.id if subscription else None,
        status=subscription.status if subscription else "free",
        starts_at=subscription.starts_at if subscription else None,
        expires_at=subscription.expires_at if subscription else None,
        plan=plan,
        product_limit=product_limit,
        product_count=product_count,
        can_add_product=product_count < product_limit,
    )


@router.post("/profile", response_model=SellerProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: SellerProfileCreate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SellerProfileResponse:
    profile = await create_seller_profile(db, current_user, payload)
    return seller_response(profile)


@router.get("/profile", response_model=SellerProfileResponse)
async def read_profile(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SellerProfileResponse:
    profile = await get_seller_profile(db, current_user)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профіль автора ще не створено.",
        )
    return seller_response(profile)


@router.patch("/profile", response_model=SellerProfileResponse)
async def patch_profile(
    payload: SellerProfileUpdate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SellerProfileResponse:
    profile = await update_seller_profile(db, current_user, payload)
    return seller_response(profile)


@router.get("/products", response_model=list[SellerProductResponse])
async def read_seller_products(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[SellerProductResponse]:
    products = await list_seller_products(db, current_user)
    return [seller_product_response(product) for product in products]


@router.get("/products/{product_id}/visibility", response_model=SellerProductVisibilityResponse)
async def read_seller_product_visibility(
    product_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SellerProductVisibilityResponse:
    return SellerProductVisibilityResponse(
        **await get_seller_product_visibility(db, current_user, product_id)
    )


@router.post("/products/{product_id}/buy-placement", response_model=SellerPlacementPurchaseResponse)
async def buy_product_placement(
    product_id: UUID,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SellerPlacementPurchaseResponse:
    placement = await buy_one_time_placement(db, current_user, product_id)
    return SellerPlacementPurchaseResponse(
        ok=True,
        placement_id=placement.id,
        product_id=placement.product_id,
        paid_amount=placement_amount_major(placement),
    )


@router.get("/placements", response_model=SellerPlacementsResponse)
async def read_seller_placements(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SellerPlacementsResponse:
    placements, total = await list_seller_placements(db, current_user, page=page, limit=limit)
    return SellerPlacementsResponse(
        items=[seller_placement_response(placement) for placement in placements],
        page=page,
        limit=limit,
        total=total,
    )


@router.get("/contact-requests", response_model=list[SellerContactRequestResponse])
async def read_seller_contact_requests(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[SellerContactRequestResponse]:
    contact_requests = await list_seller_contact_requests(db, current_user)
    return [seller_contact_request_response(contact_request) for contact_request in contact_requests]


@router.patch("/contact-requests/{contact_request_id}", response_model=SellerContactRequestResponse)
async def patch_seller_contact_request(
    contact_request_id: UUID,
    payload: SellerContactRequestUpdate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SellerContactRequestResponse:
    contact_request = await update_seller_contact_request(db, current_user, contact_request_id, payload.status)
    return seller_contact_request_response(contact_request)


@router.get("/subscription", response_model=SellerSubscriptionResponse)
async def read_seller_subscription(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SellerSubscriptionResponse:
    subscription, product_count, product_limit = await get_seller_subscription_state(db, current_user)
    return seller_subscription_response(subscription, product_count, product_limit)


@router.get("/stats", response_model=SellerStatsResponse)
async def read_seller_stats(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> SellerStatsResponse:
    return SellerStatsResponse(**await get_seller_stats(db, current_user))
