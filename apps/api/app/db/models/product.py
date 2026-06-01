from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'pending_moderation', 'published', 'rejected', 'hidden', 'deleted')",
            name="product_status_valid",
        ),
        CheckConstraint(
            "delivery_method IN ('uploaded_file', 'external_link', 'private_message')",
            name="product_delivery_method_valid",
        ),
        CheckConstraint("price_amount >= 0", name="product_price_non_negative"),
    )

    seller_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("seller_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    level: Mapped[str | None] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    audience: Mapped[str | None] = mapped_column(String(64), index=True)
    price_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="UAH")
    product_file_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
    )
    delivery_method: Mapped[str] = mapped_column(String(64), nullable=False, server_default="uploaded_file")
    external_file_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default="draft", index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    seller: Mapped["SellerProfile"] = relationship(back_populates="products")
    product_file: Mapped["File | None"] = relationship(back_populates="products")
    previews: Mapped[list["ProductPreview"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    reports: Mapped[list["ProductReport"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    view_events: Mapped[list["ProductViewEvent"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    contact_requests: Mapped[list["ContactRequest"]] = relationship(back_populates="product")
