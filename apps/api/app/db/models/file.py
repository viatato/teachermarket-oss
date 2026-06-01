from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class File(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint("file_kind IN ('product_file', 'preview_image')", name="file_kind_valid"),
    )

    owner_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    storage_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    file_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    owner: Mapped["User | None"] = relationship(back_populates="files")
    products: Mapped[list["Product"]] = relationship(back_populates="product_file")
    previews: Mapped[list["ProductPreview"]] = relationship(back_populates="file")
