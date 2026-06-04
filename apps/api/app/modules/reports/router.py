from typing import Annotated
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import DatabaseSession, get_current_user
from app.db.models import AuditLog, Product, ProductReport, SellerProfile, User
from app.modules.products.service import cleanup_catalog_subscriptions, visible_product_condition
from app.modules.reports.schemas import ProductReportCreate, ProductReportResponse


router = APIRouter(tags=["reports"])


def report_response(report: ProductReport) -> ProductReportResponse:
    return ProductReportResponse(
        id=report.id,
        product_id=report.product_id,
        reporter_id=report.reporter_id,
        reason=report.reason,
        status=report.status,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.post("/products/{product_id}/report", response_model=ProductReportResponse, status_code=status.HTTP_201_CREATED)
async def report_product(
    product_id: UUID,
    payload: ProductReportCreate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProductReportResponse:
    await cleanup_catalog_subscriptions(db)
    product = await db.scalar(
        select(Product)
        .options(selectinload(Product.seller))
        .join(SellerProfile)
        .where(Product.id == product_id, Product.status == "published", visible_product_condition(datetime.now(UTC)))
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матеріал не знайдено.")
    if product.seller.user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не можна скаржитися на власний матеріал.")
    existing = await db.scalar(
        select(ProductReport).where(ProductReport.product_id == product_id, ProductReport.reporter_id == current_user.id)
    )
    if existing is not None:
        return report_response(existing)
    report = ProductReport(product_id=product_id, reporter_id=current_user.id, reason=payload.reason.strip())
    db.add(report)
    await db.flush()
    db.add(AuditLog(actor_user_id=current_user.id, action="product_report.created", entity_type="product_report", entity_id=report.id))
    await db.commit()
    await db.refresh(report)
    return report_response(report)
