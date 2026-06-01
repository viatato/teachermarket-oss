from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import DatabaseSession, get_current_user
from app.db.models import User
from app.modules.contact_requests.schemas import ContactRequestCreate, ContactRequestResponse
from app.modules.contact_requests.service import create_contact_request
from app.security.rate_limit import rate_limit


router = APIRouter(tags=["contact_requests"])


@router.post(
    "/products/{product_id}/contact-request",
    response_model=ContactRequestResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(scope="contact_request", limit=15, window_seconds=60))],
)
async def request_contact(
    product_id: UUID,
    payload: ContactRequestCreate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContactRequestResponse:
    contact_request, seller_url = await create_contact_request(
        db,
        user=current_user,
        product_id=product_id,
        payload=payload,
    )
    return ContactRequestResponse(
        id=contact_request.id,
        product_id=contact_request.product_id,
        seller_id=contact_request.seller_id,
        seller_telegram_url=seller_url,
        status=contact_request.status,
        created_at=contact_request.created_at,
    )
