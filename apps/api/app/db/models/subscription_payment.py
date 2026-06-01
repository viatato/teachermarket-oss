from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SubscriptionPayment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subscription_payments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('created', 'paid', 'failed', 'canceled', 'expired')",
            name="subscription_payment_status_valid",
        ),
        CheckConstraint("amount >= 0", name="subscription_payment_amount_non_negative"),
    )

    seller_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("seller_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        index=True,
    )
    plan_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    payment_url: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="UAH")
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default="created", index=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)

    seller: Mapped["SellerProfile"] = relationship(back_populates="subscription_payments")
    subscription: Mapped["Subscription | None"] = relationship(back_populates="payments")
    plan: Mapped["SubscriptionPlan"] = relationship(back_populates="payments")
