from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OneTimePlacement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "one_time_placements"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'expired')", name="one_time_placement_status_valid"),
        Index(
            "uq_one_time_placements_active_product",
            "product_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    product_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    seller_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("seller_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    paid_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=4000, server_default="4000")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="UAH", server_default="UAH")
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active", server_default="active")

    product: Mapped["Product"] = relationship(back_populates="one_time_placements")
    seller: Mapped["SellerProfile"] = relationship(back_populates="one_time_placements")
