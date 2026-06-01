from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


DELIVERY_UPLOADED_FILE = "uploaded_file"
DELIVERY_EXTERNAL_LINK = "external_link"
DELIVERY_PRIVATE_MESSAGE = "private_message"
DELIVERY_METHODS = {DELIVERY_UPLOADED_FILE, DELIVERY_EXTERNAL_LINK, DELIVERY_PRIVATE_MESSAGE}


class ProductDeliveryMixin(BaseModel):
    delivery_method: str = DELIVERY_UPLOADED_FILE
    external_file_url: str | None = Field(default=None, max_length=2000)

    @field_validator("delivery_method")
    @classmethod
    def validate_delivery_method(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in DELIVERY_METHODS:
            raise ValueError("Недійсний спосіб передачі матеріалу.")
        return value

    @field_validator("external_file_url")
    @classmethod
    def clean_external_file_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


def is_http_url(value: str | None) -> bool:
    return bool(value and value.lower().startswith(("https://", "http://")))


class ProductCreate(ProductDeliveryMixin):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10, max_length=5000)
    language: str = Field(min_length=2, max_length=64)
    level: str | None = Field(default=None, max_length=64)
    category: str = Field(min_length=2, max_length=64)
    audience: str | None = Field(default=None, max_length=64)
    price_amount: int = Field(ge=0)
    currency: str = Field(default="UAH", min_length=3, max_length=3)
    product_file_id: UUID | None = None
    preview_file_ids: list[UUID] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_delivery(self) -> "ProductCreate":
        if self.delivery_method == DELIVERY_UPLOADED_FILE and self.product_file_id is None:
            raise ValueError("Для завантаженого файлу потрібен product_file_id.")
        if self.delivery_method == DELIVERY_EXTERNAL_LINK and not is_http_url(self.external_file_url):
            raise ValueError("Для посилання потрібен URL, що починається з http:// або https://.")
        if self.delivery_method != DELIVERY_EXTERNAL_LINK:
            self.external_file_url = None
        return self


class ProductUpdate(ProductDeliveryMixin):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    language: str | None = Field(default=None, min_length=2, max_length=64)
    level: str | None = Field(default=None, max_length=64)
    category: str | None = Field(default=None, min_length=2, max_length=64)
    audience: str | None = Field(default=None, max_length=64)
    price_amount: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    product_file_id: UUID | None = None
    preview_file_ids: list[UUID] | None = Field(default=None, min_length=1, max_length=3)


class ProductResponse(BaseModel):
    id: UUID
    seller_id: UUID
    title: str
    description: str
    language: str
    level: str | None = None
    category: str
    audience: str | None = None
    price_amount: int
    currency: str
    product_file_id: UUID | None = None
    delivery_method: str
    external_file_url: str | None = None
    preview_file_ids: list[UUID]
    status: str
    rejection_reason: str | None = None


class CatalogSellerResponse(BaseModel):
    id: UUID
    display_name: str
    bio: str | None = None
    contact_username: str | None = None


class CatalogProductListItem(BaseModel):
    id: UUID
    title: str
    language: str
    level: str | None = None
    category: str
    audience: str | None = None
    price_amount: int
    currency: str
    preview_file_id: UUID | None = None
    preview_url: str | None = None
    delivery_method: str
    created_at: datetime
    published_at: datetime | None = None
    seller: CatalogSellerResponse


class CatalogProductDetail(BaseModel):
    id: UUID
    title: str
    description: str
    language: str
    level: str | None = None
    category: str
    audience: str | None = None
    price_amount: int
    currency: str
    preview_file_ids: list[UUID]
    preview_urls: list[str] = Field(default_factory=list)
    delivery_method: str
    created_at: datetime
    published_at: datetime | None = None
    seller: CatalogSellerResponse
    is_favorite: bool = False


class CatalogProductsResponse(BaseModel):
    items: list[CatalogProductListItem]
    page: int
    limit: int
    total: int


class ProductViewResponse(BaseModel):
    tracked: bool
