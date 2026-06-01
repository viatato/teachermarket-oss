"""initial schema

Revision ID: 20260520_0001
Revises:
Create Date: 2026-05-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260520_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("telegram_id", name=op.f("uq_users_telegram_id")),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=False)

    op.create_table(
        "subscription_plans",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="UAH", nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("product_limit", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscription_plans")),
        sa.UniqueConstraint("code", name=op.f("uq_subscription_plans_code")),
    )
    op.create_index(op.f("ix_subscription_plans_code"), "subscription_plans", ["code"], unique=False)

    op.create_table(
        "seller_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("contact_username", sa.String(length=255), nullable=True),
        sa.Column("contact_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), server_default="active", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_seller_profiles_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_seller_profiles")),
        sa.UniqueConstraint("user_id", name=op.f("uq_seller_profiles_user_id")),
    )
    op.create_index(op.f("ix_seller_profiles_status"), "seller_profiles", ["status"], unique=False)
    op.create_index(op.f("ix_seller_profiles_user_id"), "seller_profiles", ["user_id"], unique=False)

    op.create_table(
        "files",
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("file_kind", sa.String(length=64), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name=op.f("fk_files_owner_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_files")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_files_storage_key")),
    )
    op.create_index(op.f("ix_files_file_kind"), "files", ["file_kind"], unique=False)
    op.create_index(op.f("ix_files_owner_id"), "files", ["owner_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=128), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name=op.f("fk_audit_logs_actor_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)

    op.create_table(
        "subscriptions",
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=64), server_default="active", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], name=op.f("fk_subscriptions_plan_id_subscription_plans"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["seller_id"], ["seller_profiles.id"], name=op.f("fk_subscriptions_seller_id_seller_profiles"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscriptions")),
    )
    op.create_index(op.f("ix_subscriptions_expires_at"), "subscriptions", ["expires_at"], unique=False)
    op.create_index(op.f("ix_subscriptions_plan_id"), "subscriptions", ["plan_id"], unique=False)
    op.create_index(op.f("ix_subscriptions_seller_id"), "subscriptions", ["seller_id"], unique=False)
    op.create_index(op.f("ix_subscriptions_status"), "subscriptions", ["status"], unique=False)

    op.create_table(
        "products",
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=64), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("audience", sa.String(length=64), nullable=True),
        sa.Column("price_amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="UAH", nullable=False),
        sa.Column("product_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("delivery_method", sa.String(length=64), server_default="uploaded_file", nullable=False),
        sa.Column("external_file_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), server_default="draft", nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_file_id"], ["files.id"], name=op.f("fk_products_product_file_id_files"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["seller_id"], ["seller_profiles.id"], name=op.f("fk_products_seller_id_seller_profiles"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
    )
    op.create_index(op.f("ix_products_audience"), "products", ["audience"], unique=False)
    op.create_index(op.f("ix_products_category"), "products", ["category"], unique=False)
    op.create_index(op.f("ix_products_language"), "products", ["language"], unique=False)
    op.create_index(op.f("ix_products_level"), "products", ["level"], unique=False)
    op.create_index(op.f("ix_products_published_at"), "products", ["published_at"], unique=False)
    op.create_index(op.f("ix_products_seller_id"), "products", ["seller_id"], unique=False)
    op.create_index(op.f("ix_products_status"), "products", ["status"], unique=False)
    op.create_index(
        "ix_products_catalog_filters",
        "products",
        ["status", "language", "category", "level", "audience", "published_at"],
        unique=False,
    )

    op.create_table(
        "subscription_payments",
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
        sa.Column("payment_url", sa.Text(), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="UAH", nullable=False),
        sa.Column("status", sa.String(length=64), server_default="created", nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], name=op.f("fk_subscription_payments_plan_id_subscription_plans"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["seller_id"], ["seller_profiles.id"], name=op.f("fk_subscription_payments_seller_id_seller_profiles"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], name=op.f("fk_subscription_payments_subscription_id_subscriptions"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscription_payments")),
        sa.UniqueConstraint("provider_payment_id", name=op.f("uq_subscription_payments_provider_payment_id")),
    )
    op.create_index(op.f("ix_subscription_payments_plan_id"), "subscription_payments", ["plan_id"], unique=False)
    op.create_index(op.f("ix_subscription_payments_seller_id"), "subscription_payments", ["seller_id"], unique=False)
    op.create_index(op.f("ix_subscription_payments_status"), "subscription_payments", ["status"], unique=False)
    op.create_index(op.f("ix_subscription_payments_subscription_id"), "subscription_payments", ["subscription_id"], unique=False)

    op.create_table(
        "product_previews",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], name=op.f("fk_product_previews_file_id_files"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_product_previews_product_id_products"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_previews")),
    )
    op.create_index(op.f("ix_product_previews_product_id"), "product_previews", ["product_id"], unique=False)

    op.create_table(
        "favorites",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_favorites_product_id_products"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_favorites_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_favorites")),
        sa.UniqueConstraint("user_id", "product_id", name="uq_favorites_user_product"),
    )
    op.create_index(op.f("ix_favorites_product_id"), "favorites", ["product_id"], unique=False)
    op.create_index(op.f("ix_favorites_user_id"), "favorites", ["user_id"], unique=False)

    op.create_table(
        "reviews",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name=op.f("ck_reviews_rating_range")),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"], name=op.f("fk_reviews_buyer_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_reviews_product_id_products"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
    )
    op.create_index(op.f("ix_reviews_buyer_id"), "reviews", ["buyer_id"], unique=False)
    op.create_index(op.f("ix_reviews_product_id"), "reviews", ["product_id"], unique=False)

    op.create_table(
        "contact_requests",
        sa.Column("requester_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requester_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("requester_username", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_contact_requests_product_id_products"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], name=op.f("fk_contact_requests_requester_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["seller_id"], ["seller_profiles.id"], name=op.f("fk_contact_requests_seller_id_seller_profiles"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contact_requests")),
    )
    op.create_index(op.f("ix_contact_requests_product_id"), "contact_requests", ["product_id"], unique=False)
    op.create_index(op.f("ix_contact_requests_requester_id"), "contact_requests", ["requester_id"], unique=False)
    op.create_index(op.f("ix_contact_requests_seller_id"), "contact_requests", ["seller_id"], unique=False)
    op.create_index("ix_contact_requests_seller_created", "contact_requests", ["seller_id", "created_at"], unique=False)
    op.create_index("ix_contact_requests_product_created", "contact_requests", ["product_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_contact_requests_product_created", table_name="contact_requests")
    op.drop_index("ix_contact_requests_seller_created", table_name="contact_requests")
    op.drop_index(op.f("ix_contact_requests_seller_id"), table_name="contact_requests")
    op.drop_index(op.f("ix_contact_requests_requester_id"), table_name="contact_requests")
    op.drop_index(op.f("ix_contact_requests_product_id"), table_name="contact_requests")
    op.drop_table("contact_requests")

    op.drop_index(op.f("ix_reviews_product_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_buyer_id"), table_name="reviews")
    op.drop_table("reviews")

    op.drop_index(op.f("ix_favorites_user_id"), table_name="favorites")
    op.drop_index(op.f("ix_favorites_product_id"), table_name="favorites")
    op.drop_table("favorites")

    op.drop_index(op.f("ix_product_previews_product_id"), table_name="product_previews")
    op.drop_table("product_previews")

    op.drop_index(op.f("ix_subscription_payments_subscription_id"), table_name="subscription_payments")
    op.drop_index(op.f("ix_subscription_payments_status"), table_name="subscription_payments")
    op.drop_index(op.f("ix_subscription_payments_seller_id"), table_name="subscription_payments")
    op.drop_index(op.f("ix_subscription_payments_plan_id"), table_name="subscription_payments")
    op.drop_table("subscription_payments")

    op.drop_index("ix_products_catalog_filters", table_name="products")
    op.drop_index(op.f("ix_products_status"), table_name="products")
    op.drop_index(op.f("ix_products_seller_id"), table_name="products")
    op.drop_index(op.f("ix_products_published_at"), table_name="products")
    op.drop_index(op.f("ix_products_level"), table_name="products")
    op.drop_index(op.f("ix_products_language"), table_name="products")
    op.drop_index(op.f("ix_products_category"), table_name="products")
    op.drop_index(op.f("ix_products_audience"), table_name="products")
    op.drop_table("products")

    op.drop_index(op.f("ix_subscriptions_status"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_seller_id"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_plan_id"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_expires_at"), table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_files_owner_id"), table_name="files")
    op.drop_index(op.f("ix_files_file_kind"), table_name="files")
    op.drop_table("files")

    op.drop_index(op.f("ix_seller_profiles_user_id"), table_name="seller_profiles")
    op.drop_index(op.f("ix_seller_profiles_status"), table_name="seller_profiles")
    op.drop_table("seller_profiles")

    op.drop_index(op.f("ix_subscription_plans_code"), table_name="subscription_plans")
    op.drop_table("subscription_plans")

    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
