from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ContactRequestCreate(BaseModel):
    message: str | None = Field(default=None, max_length=1000)


class ContactRequestResponse(BaseModel):
    id: UUID
    product_id: UUID
    seller_id: UUID
    seller_telegram_url: str
    status: str = "new"
    created_at: datetime
