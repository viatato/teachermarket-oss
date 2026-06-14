"""one time placement

Revision ID: 20260604_0005
Revises: 20260529_0004
Create Date: 2026-06-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260604_0005"
down_revision: Union[str, None] = "20260529_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "one_time_placements",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paid_amount", sa.Integer(), server_default="4000", nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="UAH", nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(length=64), server_default="active", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'expired')",
            name=op.f("ck_one_time_placements_one_time_placement_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_one_time_placements_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["seller_profiles.id"],
            name=op.f("fk_one_time_placements_seller_id_seller_profiles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_one_time_placements")),
    )
    op.create_index(
        "ix_one_time_placements_product_id_status",
        "one_time_placements",
        ["product_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_one_time_placements_seller_id_status",
        "one_time_placements",
        ["seller_id", "status"],
        unique=False,
    )
    op.create_index(
        "uq_one_time_placements_active_product",
        "one_time_placements",
        ["product_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_one_time_placements_active_product", table_name="one_time_placements")
    op.drop_index("ix_one_time_placements_seller_id_status", table_name="one_time_placements")
    op.drop_index("ix_one_time_placements_product_id_status", table_name="one_time_placements")
    op.drop_table("one_time_placements")
