from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SubscriptionPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subscription_plans"

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="UAH")
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    product_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")
    payments: Mapped[list["SubscriptionPayment"]] = relationship(back_populates="plan")
