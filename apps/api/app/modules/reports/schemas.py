from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProductReportCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


class ProductReportResponse(BaseModel):
    id: UUID
    product_id: UUID
    reporter_id: UUID
    reason: str
    status: str
    created_at: datetime
    updated_at: datetime
