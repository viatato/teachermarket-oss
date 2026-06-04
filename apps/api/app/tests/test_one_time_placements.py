import asyncio
import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

from fastapi.routing import APIRoute
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects import postgresql

from app.db.models import OneTimePlacement, Product, User
from app.dependencies import get_current_user, require_admin
from app.main import create_app
from app.modules.products.service import FREE_VISIBLE_PRODUCT_LIMIT, visible_product_condition
from app.modules.sellers.router import buy_product_placement, read_seller_placements
from app.modules.sellers.service import ONE_TIME_PLACEMENT_AMOUNT, buy_one_time_placement
from app.modules.subscriptions.service import activate_or_extend_subscription, subscription_visibility_cutoff


class PlacementFeatureTests(unittest.TestCase):
    def compile_visibility_sql(self) -> str:
        now = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
        return str(
            visible_product_condition(now).compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

    def test_buy_placement_creates_active_mock_paid_record_for_owner_product(self) -> None:
        async def run_check() -> tuple[OneTimePlacement, UUID, int, int]:
            class FakeDb:
                def __init__(self, product: Product):
                    self.values = [product, None]
                    self.added = []
                    self.commits = 0

                async def scalar(self, _query):
                    return self.values.pop(0)

                def add(self, item):
                    self.added.append(item)

                async def flush(self):
                    for item in self.added:
                        if isinstance(item, OneTimePlacement) and item.id is None:
                            item.id = uuid4()

                async def commit(self):
                    self.commits += 1

                async def refresh(self, _item):
                    pass

            seller_id = uuid4()
            product = Product(id=uuid4(), seller_id=seller_id, status="published")
            user = User(id=uuid4(), telegram_id=123)
            db = FakeDb(product)
            with patch(
                "app.modules.sellers.service.require_seller_profile",
                AsyncMock(return_value=SimpleNamespace(id=seller_id)),
            ):
                placement = await buy_one_time_placement(db, user, product.id)
            return placement, product.id, db.commits, len(db.added)

        placement, product_id, commits, added_count = asyncio.run(run_check())
        self.assertEqual(placement.product_id, product_id)
        self.assertEqual(placement.paid_amount, ONE_TIME_PLACEMENT_AMOUNT)
        self.assertEqual(placement.currency, "UAH")
        self.assertEqual(placement.status, "active")
        self.assertEqual(commits, 1)
        self.assertEqual(added_count, 2)

    def test_buy_placement_is_idempotent_for_active_existing_placement(self) -> None:
        async def run_check() -> tuple[bool, int, int]:
            class FakeDb:
                def __init__(self, product: Product, placement: OneTimePlacement):
                    self.values = [product, placement]
                    self.added = []
                    self.commits = 0

                async def scalar(self, _query):
                    return self.values.pop(0)

                def add(self, item):
                    self.added.append(item)

                async def flush(self):
                    raise AssertionError("Existing placement should not create a new row.")

                async def commit(self):
                    self.commits += 1

                async def refresh(self, _item):
                    pass

            seller_id = uuid4()
            product = Product(id=uuid4(), seller_id=seller_id, status="published")
            existing = OneTimePlacement(
                id=uuid4(),
                product_id=product.id,
                seller_id=seller_id,
                paid_amount=ONE_TIME_PLACEMENT_AMOUNT,
                currency="UAH",
                status="active",
            )
            db = FakeDb(product, existing)
            with patch(
                "app.modules.sellers.service.require_seller_profile",
                AsyncMock(return_value=SimpleNamespace(id=seller_id)),
            ):
                placement = await buy_one_time_placement(db, User(id=uuid4(), telegram_id=123), product.id)
            return placement is existing, db.commits, len(db.added)

        self.assertEqual(asyncio.run(run_check()), (True, 0, 0))

    def test_buy_placement_recovers_from_concurrent_active_insert(self) -> None:
        async def run_check() -> tuple[bool, int, int, int]:
            class FakeDb:
                def __init__(self, product: Product, placement: OneTimePlacement):
                    self.values = [product, None, placement]
                    self.added = []
                    self.commits = 0
                    self.rollbacks = 0

                async def scalar(self, _query):
                    return self.values.pop(0)

                def add(self, item):
                    self.added.append(item)

                async def flush(self):
                    raise IntegrityError("insert placement", {}, Exception("duplicate active placement"))

                async def commit(self):
                    self.commits += 1

                async def rollback(self):
                    self.rollbacks += 1

                async def refresh(self, _item):
                    pass

            seller_id = uuid4()
            product = Product(id=uuid4(), seller_id=seller_id, status="published")
            existing = OneTimePlacement(
                id=uuid4(),
                product_id=product.id,
                seller_id=seller_id,
                paid_amount=ONE_TIME_PLACEMENT_AMOUNT,
                currency="UAH",
                status="active",
            )
            db = FakeDb(product, existing)
            with patch(
                "app.modules.sellers.service.require_seller_profile",
                AsyncMock(return_value=SimpleNamespace(id=seller_id)),
            ):
                placement = await buy_one_time_placement(db, User(id=uuid4(), telegram_id=123), product.id)
            return placement is existing, db.commits, db.rollbacks, len(db.added)

        self.assertEqual(asyncio.run(run_check()), (True, 0, 1, 1))

    def test_seller_placement_routes_require_current_user_not_admin(self) -> None:
        app = create_app()
        for endpoint in (buy_product_placement, read_seller_placements):
            route = next(route for route in app.routes if isinstance(route, APIRoute) and route.endpoint is endpoint)
            dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
            self.assertIn(get_current_user, dependency_calls)
            self.assertNotIn(require_admin, dependency_calls)

    def test_placement_visibility_without_subscription_is_in_catalog_predicate(self) -> None:
        sql = self.compile_visibility_sql()
        self.assertIn("one_time_placements.product_id = products.id", sql)
        self.assertIn("one_time_placements.status = 'active'", sql)

    def test_paid_subscription_grace_visibility_uses_seven_day_cutoff(self) -> None:
        now = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
        cutoff = subscription_visibility_cutoff(now)
        self.assertEqual(cutoff, datetime(2026, 5, 28, 12, 0, tzinfo=UTC))
        sql = self.compile_visibility_sql()
        self.assertIn("subscription_plans.price_amount > 0", sql)
        self.assertIn("subscriptions.status IN ('active', 'trial')", sql)
        self.assertIn("subscriptions.expires_at >= '2026-05-28 12:00:00+00:00'", sql)

    def test_subscription_after_grace_is_hidden_by_cutoff(self) -> None:
        now = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
        within_grace = now - timedelta(days=6, hours=23)
        at_cutoff = now - timedelta(days=7)
        after_grace = now - timedelta(days=7, minutes=1)
        cutoff = subscription_visibility_cutoff(now)
        self.assertGreater(within_grace, cutoff)
        self.assertEqual(at_cutoff, cutoff)
        self.assertLess(after_grace, cutoff)

    def test_renewal_during_grace_reactivates_existing_subscription(self) -> None:
        async def run_check():
            plan_id = uuid4()
            seller_id = uuid4()
            previous_expiry = datetime.now(UTC) - timedelta(days=2)
            existing = SimpleNamespace(
                id=uuid4(),
                plan_id=uuid4(),
                status="active",
                expires_at=previous_expiry,
            )
            payment = SimpleNamespace(
                seller_id=seller_id,
                plan_id=plan_id,
                plan=SimpleNamespace(id=plan_id, duration_days=30),
            )

            class FakeDb:
                async def flush(self):
                    pass

            with (
                patch("app.modules.subscriptions.service.expire_stale_subscriptions", AsyncMock(return_value=0)),
                patch(
                    "app.modules.subscriptions.service.get_current_subscription_by_seller_id",
                    AsyncMock(return_value=existing),
                ),
            ):
                renewed = await activate_or_extend_subscription(FakeDb(), payment)
            return previous_expiry, renewed

        previous_expiry, renewed = asyncio.run(run_check())
        self.assertEqual(renewed.status, "active")
        self.assertGreater(renewed.expires_at, previous_expiry)
        self.assertGreater(renewed.expires_at, datetime.now(UTC) + timedelta(days=29))

    def test_first_three_published_products_are_free_tier_visible(self) -> None:
        sql = self.compile_visibility_sql()
        self.assertIn("products_1.status = 'published'", sql)
        self.assertIn("products_1.created_at < products.created_at", sql)
        self.assertIn("products_1.id <= products.id", sql)
        self.assertIn(f"<= {FREE_VISIBLE_PRODUCT_LIMIT}", sql)


if __name__ == "__main__":
    unittest.main()
