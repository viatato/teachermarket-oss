from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SellerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seller_profiles"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'suspended')", name="seller_profile_status_valid"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    contact_username: Mapped[str | None] = mapped_column(String(255))
    contact_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default="active", index=True)

    user: Mapped["User"] = relationship(back_populates="seller_profile")
    products: Mapped[list["Product"]] = relationship(back_populates="seller")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="seller")
    subscription_payments: Mapped[list["SubscriptionPayment"]] = relationship(back_populates="seller")
    contact_requests: Mapped[list["ContactRequest"]] = relationship(back_populates="seller")
