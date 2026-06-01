"""add product delivery method

Revision ID: 20260521_0002
Revises: 20260520_0001
Create Date: 2026-05-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260521_0002"
down_revision: Union[str, None] = "20260520_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_columns = {column["name"] for column in sa.inspect(bind).get_columns("products")}
    if "delivery_method" not in existing_columns:
        op.add_column(
            "products",
            sa.Column("delivery_method", sa.String(length=64), server_default="uploaded_file", nullable=False),
        )
    if "external_file_url" not in existing_columns:
        op.add_column("products", sa.Column("external_file_url", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    existing_columns = {column["name"] for column in sa.inspect(bind).get_columns("products")}
    if "external_file_url" in existing_columns:
        op.drop_column("products", "external_file_url")
    if "delivery_method" in existing_columns:
        op.drop_column("products", "delivery_method")
