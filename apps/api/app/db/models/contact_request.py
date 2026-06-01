from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class ContactRequest(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "contact_requests"
    __table_args__ = (
        CheckConstraint("status IN ('new', 'handled', 'archived')", name="contact_request_status_valid"),
        UniqueConstraint("requester_id", "product_id", name="uq_contact_requests_requester_product"),
    )

    requester_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("seller_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requester_telegram_id: Mapped[int | None] = mapped_column(BigInteger)
    requester_username: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default="new", index=True)

    requester: Mapped["User | None"] = relationship(back_populates="contact_requests")
    product: Mapped["Product"] = relationship(back_populates="contact_requests")
    seller: Mapped["SellerProfile"] = relationship(back_populates="contact_requests")
