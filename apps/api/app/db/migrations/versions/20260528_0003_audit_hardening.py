"""audit hardening

Revision ID: 20260528_0003
Revises: 20260521_0002
Create Date: 2026-05-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260528_0003"
down_revision: Union[str, None] = "20260521_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    if "status" not in _columns("contact_requests"):
        op.add_column(
            "contact_requests",
            sa.Column("status", sa.String(length=64), server_default="new", nullable=False),
        )
        op.create_index(op.f("ix_contact_requests_status"), "contact_requests", ["status"], unique=False)

    op.execute("UPDATE subscriptions SET status = 'expired' WHERE status IN ('active', 'trial') AND expires_at IS NOT NULL AND expires_at <= now()")

    op.create_check_constraint(
        op.f("ck_products_product_status_valid"),
        "products",
        "status IN ('draft', 'pending_moderation', 'published', 'rejected', 'hidden', 'deleted')",
    )
    op.create_check_constraint(
        op.f("ck_products_product_delivery_method_valid"),
        "products",
        "delivery_method IN ('uploaded_file', 'external_link', 'private_message')",
    )
    op.create_check_constraint(op.f("ck_products_product_price_non_negative"), "products", "price_amount >= 0")
    op.create_check_constraint(
        op.f("ck_seller_profiles_seller_profile_status_valid"),
        "seller_profiles",
        "status IN ('active', 'suspended')",
    )
    op.create_check_constraint(
        op.f("ck_subscriptions_subscription_status_valid"),
        "subscriptions",
        "status IN ('active', 'trial', 'expired', 'canceled')",
    )
    op.create_check_constraint(
        op.f("ck_subscription_payments_subscription_payment_status_valid"),
        "subscription_payments",
        "status IN ('created', 'paid', 'failed', 'canceled', 'expired')",
    )
    op.create_check_constraint(
        op.f("ck_subscription_payments_subscription_payment_amount_non_negative"),
        "subscription_payments",
        "amount >= 0",
    )
    op.create_check_constraint(op.f("ck_files_file_kind_valid"), "files", "file_kind IN ('product_file', 'preview_image')")
    op.create_check_constraint(
        op.f("ck_contact_requests_contact_request_status_valid"),
        "contact_requests",
        "status IN ('new', 'handled', 'archived')",
    )
    op.create_unique_constraint(
        "uq_reviews_buyer_product",
        "reviews",
        ["buyer_id", "product_id"],
    )
    op.create_unique_constraint(
        "uq_contact_requests_requester_product",
        "contact_requests",
        ["requester_id", "product_id"],
    )
    op.create_index(
        "uq_subscriptions_one_active_per_seller",
        "subscriptions",
        ["seller_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('active', 'trial')"),
    )

    op.create_table(
        "product_reports",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), server_default="open", nullable=False),
        sa.Column("resolved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('open', 'resolved')", name=op.f("ck_product_reports_product_report_status_valid")),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_product_reports_product_id_products"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], name=op.f("fk_product_reports_reporter_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"], name=op.f("fk_product_reports_resolved_by_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_reports")),
        sa.UniqueConstraint("reporter_id", "product_id", name="uq_product_reports_reporter_product"),
    )
    op.create_index(op.f("ix_product_reports_product_id"), "product_reports", ["product_id"], unique=False)
    op.create_index(op.f("ix_product_reports_reporter_id"), "product_reports", ["reporter_id"], unique=False)
    op.create_index(op.f("ix_product_reports_status"), "product_reports", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_product_reports_status"), table_name="product_reports")
    op.drop_index(op.f("ix_product_reports_reporter_id"), table_name="product_reports")
    op.drop_index(op.f("ix_product_reports_product_id"), table_name="product_reports")
    op.drop_table("product_reports")
    op.drop_index("uq_subscriptions_one_active_per_seller", table_name="subscriptions")
    op.drop_constraint("uq_contact_requests_requester_product", "contact_requests", type_="unique")
    op.drop_constraint("uq_reviews_buyer_product", "reviews", type_="unique")
    op.drop_constraint(op.f("ck_contact_requests_contact_request_status_valid"), "contact_requests", type_="check")
    op.drop_constraint(op.f("ck_files_file_kind_valid"), "files", type_="check")
    op.drop_constraint(op.f("ck_subscription_payments_subscription_payment_amount_non_negative"), "subscription_payments", type_="check")
    op.drop_constraint(op.f("ck_subscription_payments_subscription_payment_status_valid"), "subscription_payments", type_="check")
    op.drop_constraint(op.f("ck_subscriptions_subscription_status_valid"), "subscriptions", type_="check")
    op.drop_constraint(op.f("ck_seller_profiles_seller_profile_status_valid"), "seller_profiles", type_="check")
    op.drop_constraint(op.f("ck_products_product_price_non_negative"), "products", type_="check")
    op.drop_constraint(op.f("ck_products_product_delivery_method_valid"), "products", type_="check")
    op.drop_constraint(op.f("ck_products_product_status_valid"), "products", type_="check")
    if "status" in _columns("contact_requests"):
        op.drop_index(op.f("ix_contact_requests_status"), table_name="contact_requests")
        op.drop_column("contact_requests", "status")
