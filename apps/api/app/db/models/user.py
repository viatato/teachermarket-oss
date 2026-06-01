from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    language_code: Mapped[str | None] = mapped_column(String(16))
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    seller_profile: Mapped["SellerProfile | None"] = relationship(back_populates="user")
    files: Mapped[list["File"]] = relationship(back_populates="owner")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="buyer")
    contact_requests: Mapped[list["ContactRequest"]] = relationship(back_populates="requester")
    product_reports: Mapped[list["ProductReport"]] = relationship(
        back_populates="reporter",
        foreign_keys="ProductReport.reporter_id",
    )
    product_view_events: Mapped[list["ProductViewEvent"]] = relationship(back_populates="viewer")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="actor")
