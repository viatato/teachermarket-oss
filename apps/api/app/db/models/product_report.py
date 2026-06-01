from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProductReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_reports"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'resolved')", name="product_report_status_valid"),
        UniqueConstraint("reporter_id", "product_id", name="uq_product_reports_reporter_product"),
    )

    product_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reporter_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default="open", index=True)
    resolved_by_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    product: Mapped["Product"] = relationship(back_populates="reports")
    reporter: Mapped["User"] = relationship(back_populates="product_reports", foreign_keys=[reporter_id])
    resolved_by: Mapped["User | None"] = relationship(foreign_keys=[resolved_by_user_id])
