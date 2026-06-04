import asyncio
import os
import unittest
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException
from fastapi.routing import APIRoute
from sqlalchemy.dialects import postgresql

from app.config import get_settings
from app.db.models import User
from app.dependencies import get_current_user, require_admin
from app.main import create_app
from app.modules.admin.router import (
    admin_reports,
    admin_subscription_plans,
    require_admin_reports_enabled,
    require_admin_subscriptions_enabled,
)
from app.modules.admin.service import list_product_reports, list_subscription_plans
from app.modules.products.service import visible_product_condition
from app.modules.reports.router import require_reports_enabled
from app.modules.reviews.router import post_review, require_reviews_enabled
from app.modules.sellers.router import buy_product_placement, read_seller_subscription
from app.modules.sellers.service import buy_one_time_placement, ensure_placements_enabled, list_seller_placements
from app.modules.subscriptions.router import checkout_subscription, mark_paid, subscription_plans
from app.modules.subscriptions.service import ensure_subscriptions_enabled


class NoDbAccess:
    def __getattr__(self, name):
        raise AssertionError(f"Disabled feature should not access db.{name}.")


class FeatureFlagTests(unittest.TestCase):
    def setUp(self) -> None:
        get_settings.cache_clear()

    def tearDown(self) -> None:
        get_settings.cache_clear()

    def dependency_calls_for(self, endpoint) -> set:
        app = create_app()
        route = next(route for route in app.routes if isinstance(route, APIRoute) and route.endpoint is endpoint)
        return {dependency.call for dependency in route.dependant.dependencies}

    def compile_visibility_sql(self) -> str:
        now = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
        return str(
            visible_product_condition(now).compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

    def assert_disabled_404(self, callable_) -> None:
        with self.assertRaises(HTTPException) as ctx:
            callable_()
        self.assertEqual(ctx.exception.status_code, 404)

    def test_feature_flags_default_to_enabled(self) -> None:
        settings = get_settings()
        self.assertTrue(settings.feature_subscriptions_enabled)
        self.assertTrue(settings.feature_placements_enabled)
        self.assertTrue(settings.feature_reviews_enabled)
        self.assertTrue(settings.feature_reports_enabled)

    def test_disabled_feature_guards_return_404_before_service_work(self) -> None:
        with patch.dict(
            os.environ,
            {
                "FEATURE_SUBSCRIPTIONS_ENABLED": "false",
                "FEATURE_PLACEMENTS_ENABLED": "false",
                "FEATURE_REVIEWS_ENABLED": "false",
                "FEATURE_REPORTS_ENABLED": "false",
            },
        ):
            get_settings.cache_clear()
            self.assert_disabled_404(ensure_subscriptions_enabled)
            self.assert_disabled_404(ensure_placements_enabled)
            self.assert_disabled_404(require_reviews_enabled)
            self.assert_disabled_404(require_reports_enabled)
            self.assert_disabled_404(require_admin_subscriptions_enabled)
            self.assert_disabled_404(require_admin_reports_enabled)

            user = User(id=uuid4(), telegram_id=123)
            with self.assertRaises(HTTPException) as placement_ctx:
                asyncio.run(buy_one_time_placement(NoDbAccess(), user, uuid4()))
            self.assertEqual(placement_ctx.exception.status_code, 404)
            with self.assertRaises(HTTPException) as placements_ctx:
                asyncio.run(list_seller_placements(NoDbAccess(), user))
            self.assertEqual(placements_ctx.exception.status_code, 404)
            with self.assertRaises(HTTPException) as plans_ctx:
                asyncio.run(list_subscription_plans(NoDbAccess()))
            self.assertEqual(plans_ctx.exception.status_code, 404)
            with self.assertRaises(HTTPException) as reports_ctx:
                asyncio.run(list_product_reports(NoDbAccess()))
            self.assertEqual(reports_ctx.exception.status_code, 404)

    def test_feature_route_dependencies_keep_existing_auth_shape(self) -> None:
        subscription_plan_deps = self.dependency_calls_for(subscription_plans)
        self.assertIn(ensure_subscriptions_enabled, subscription_plan_deps)

        checkout_deps = self.dependency_calls_for(checkout_subscription)
        self.assertIn(ensure_subscriptions_enabled, checkout_deps)
        self.assertIn(get_current_user, checkout_deps)

        mock_paid_deps = self.dependency_calls_for(mark_paid)
        self.assertIn(ensure_subscriptions_enabled, mock_paid_deps)
        self.assertIn(require_admin, mock_paid_deps)

        placement_deps = self.dependency_calls_for(buy_product_placement)
        self.assertIn(ensure_placements_enabled, placement_deps)
        self.assertIn(get_current_user, placement_deps)

        seller_subscription_deps = self.dependency_calls_for(read_seller_subscription)
        self.assertIn(ensure_subscriptions_enabled, seller_subscription_deps)
        self.assertIn(get_current_user, seller_subscription_deps)

        review_deps = self.dependency_calls_for(post_review)
        self.assertIn(require_reviews_enabled, review_deps)
        self.assertIn(get_current_user, review_deps)

        admin_subscription_deps = self.dependency_calls_for(admin_subscription_plans)
        self.assertIn(require_admin_subscriptions_enabled, admin_subscription_deps)
        self.assertIn(require_admin, admin_subscription_deps)

        admin_reports_deps = self.dependency_calls_for(admin_reports)
        self.assertIn(require_admin_reports_enabled, admin_reports_deps)
        self.assertIn(require_admin, admin_reports_deps)

    def test_visibility_predicate_ignores_disabled_optional_modules(self) -> None:
        default_sql = self.compile_visibility_sql()
        self.assertIn("subscriptions.seller_id = products.seller_id", default_sql)
        self.assertIn("one_time_placements.product_id = products.id", default_sql)

        with patch.dict(os.environ, {"FEATURE_SUBSCRIPTIONS_ENABLED": "false", "FEATURE_PLACEMENTS_ENABLED": "false"}):
            get_settings.cache_clear()
            disabled_sql = self.compile_visibility_sql()
        self.assertNotIn("subscriptions.seller_id = products.seller_id", disabled_sql)
        self.assertNotIn("one_time_placements.product_id = products.id", disabled_sql)
        self.assertIn("products_1.status = 'published'", disabled_sql)

