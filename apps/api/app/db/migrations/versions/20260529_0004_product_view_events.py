"""product view events

Revision ID: 20260529_0004
Revises: 20260528_0003
Create Date: 2026-05-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260529_0004"
down_revision: Union[str, None] = "20260528_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_view_events",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("viewer_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("anonymous_key", sa.String(length=128), nullable=True),
        sa.Column("view_day", sa.Date(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_product_view_events_product_id_products"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["viewer_user_id"], ["users.id"], name=op.f("fk_product_view_events_viewer_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_view_events")),
    )
    op.create_index("ix_product_view_events_product_id", "product_view_events", ["product_id"], unique=False)
    op.create_index("ix_product_view_events_created_at", "product_view_events", ["created_at"], unique=False)
    op.create_index(
        "uq_product_view_events_user_day",
        "product_view_events",
        ["product_id", "viewer_user_id", "view_day"],
        unique=True,
        postgresql_where=sa.text("viewer_user_id IS NOT NULL"),
    )
    op.create_index(
        "uq_product_view_events_anon_day",
        "product_view_events",
        ["product_id", "anonymous_key", "view_day"],
        unique=True,
        postgresql_where=sa.text("viewer_user_id IS NULL AND anonymous_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_product_view_events_anon_day", table_name="product_view_events")
    op.drop_index("uq_product_view_events_user_day", table_name="product_view_events")
    op.drop_index("ix_product_view_events_created_at", table_name="product_view_events")
    op.drop_index("ix_product_view_events_product_id", table_name="product_view_events")
    op.drop_table("product_view_events")
