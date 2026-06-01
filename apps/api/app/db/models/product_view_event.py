from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class ProductViewEvent(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "product_view_events"
    __table_args__ = (
        Index("ix_product_view_events_product_id", "product_id"),
        Index("ix_product_view_events_created_at", "created_at"),
        Index(
            "uq_product_view_events_user_day",
            "product_id",
            "viewer_user_id",
            "view_day",
            unique=True,
            postgresql_where=text("viewer_user_id IS NOT NULL"),
        ),
        Index(
            "uq_product_view_events_anon_day",
            "product_id",
            "anonymous_key",
            "view_day",
            unique=True,
            postgresql_where=text("viewer_user_id IS NULL AND anonymous_key IS NOT NULL"),
        ),
    )

    product_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    viewer_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    anonymous_key: Mapped[str | None] = mapped_column(String(128))
    view_day: Mapped[date] = mapped_column(Date, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="view_events")
    viewer: Mapped["User | None"] = relationship(back_populates="product_view_events")
