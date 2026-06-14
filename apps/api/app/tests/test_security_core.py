import asyncio
import hashlib
import hmac
import json
import os
import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import urlencode
from uuid import UUID, uuid4

from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.config import get_settings, validate_runtime_settings
from app.db.models import Subscription, SubscriptionPayment, SubscriptionPlan, User
from app.dependencies import require_admin
from app.main import create_app
from app.modules.admin.router import download_admin_file, read_admin_product
from app.modules.admin.service import approve_product, hide_product, notify_author_about_moderation, restore_product
from app.modules.auth.security import create_access_token, decode_access_token
from app.modules.auth.telegram import verify_telegram_init_data
from app.modules.contact_requests.service import seller_telegram_url
from app.modules.files.service import PRODUCT_FILE_KIND, validate_extension, validate_size
from app.modules.products.router import view_product
from app.modules.products.schemas import CatalogProductDetail, CatalogProductListItem, ProductCreate
from app.modules.products.service import anonymous_view_key, delete_product, submit_product, track_product_view, update_product
from app.modules.subscriptions.router import mark_paid
from app.modules.subscriptions.service import activate_or_extend_subscription, mark_mock_payment_paid, validate_webhook_event
from app.security.rate_limit import rate_limit
from app.services.payments.base import PaymentWebhookEvent
from app.services.payments.mock import MockPaymentProvider
from app.services.payments.wayforpay import (
    WayForPayProvider,
    amount_to_wayforpay,
    request_signature,
    wayforpay_amount_to_minor_units,
)


def signed_init_data(user: dict, *, auth_date: int | None = None) -> str:
    settings = get_settings()
    payload = {
        "auth_date": str(auth_date or int(datetime.now(UTC).timestamp())),
        "query_id": "test-query",
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", settings.telegram_bot_token.encode("utf-8"), hashlib.sha256).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return urlencode(payload)


class SecurityCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        get_settings.cache_clear()

    def test_telegram_init_data_verifies_signed_user(self) -> None:
        user = {"id": 123456, "username": "teacher_test", "first_name": "Тест"}
        verified = verify_telegram_init_data(signed_init_data(user))
        self.assertEqual(verified["id"], user["id"])
        self.assertEqual(verified["username"], user["username"])

    def test_telegram_init_data_rejects_bad_hash(self) -> None:
        init_data = signed_init_data({"id": 123456}).replace("hash=", "hash=bad")
        with self.assertRaises(HTTPException) as ctx:
            verify_telegram_init_data(init_data)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_telegram_init_data_rejects_expired_auth_date(self) -> None:
        expired_auth_date = int((datetime.now(UTC) - timedelta(days=2)).timestamp())
        init_data = signed_init_data({"id": 123456}, auth_date=expired_auth_date)
        with self.assertRaises(HTTPException) as ctx:
            verify_telegram_init_data(init_data)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_telegram_init_data_rejects_future_auth_date(self) -> None:
        future_auth_date = int((datetime.now(UTC) + timedelta(minutes=10)).timestamp())
        init_data = signed_init_data({"id": 123456}, auth_date=future_auth_date)
        with self.assertRaises(HTTPException) as ctx:
            verify_telegram_init_data(init_data)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_jwt_roundtrip_and_tamper_rejection(self) -> None:
        token = create_access_token(str(uuid4()))
        payload = decode_access_token(token)
        self.assertIn("sub", payload)

        token_parts = token.split(".")
        token_parts[1] = token_parts[1][:-1] + ("a" if token_parts[1][-1] != "a" else "b")
        tampered = ".".join(token_parts)
        with self.assertRaises(HTTPException) as ctx:
            decode_access_token(tampered)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_product_delivery_method_validation(self) -> None:
        payload = {
            "title": "Test material",
            "description": "Long enough description",
            "language": "english",
            "category": "worksheet",
            "price_amount": 1000,
            "preview_file_ids": [uuid4()],
        }
        self.assertEqual(
            ProductCreate(**payload, product_file_id=uuid4()).delivery_method,
            "uploaded_file",
        )
        self.assertEqual(
            ProductCreate(
                **payload,
                delivery_method="external_link",
                external_file_url="https://example.com/material.pdf",
            ).delivery_method,
            "external_link",
        )
        self.assertEqual(
            ProductCreate(**payload, delivery_method="private_message").delivery_method,
            "private_message",
        )
        with self.assertRaises(ValueError):
            ProductCreate(**payload)

    def test_catalog_response_schemas_do_not_expose_private_file_id(self) -> None:
        self.assertNotIn("product_file_id", CatalogProductListItem.model_fields)
        self.assertNotIn("product_file_id", CatalogProductDetail.model_fields)

    def test_seller_telegram_url_prefers_explicit_contact_url(self) -> None:
        self.assertEqual(
            seller_telegram_url(SimpleNamespace(contact_url="https://example.com/contact", contact_username="teacher")),
            "https://example.com/contact",
        )
        self.assertEqual(
            seller_telegram_url(SimpleNamespace(contact_url=None, contact_username="@teacher")),
            "https://t.me/teacher",
        )

    def test_non_admin_is_rejected(self) -> None:
        user = User(telegram_id=111, username="not_admin")
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(require_admin(user))
        self.assertEqual(ctx.exception.status_code, 403)

    def test_production_docs_are_disabled(self) -> None:
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "API_BASE_URL": "https://market.example.com",
                "WEBAPP_URL": "https://market.example.com",
                "CORS_ALLOWED_ORIGINS": "https://market.example.com",
                "TELEGRAM_BOT_TOKEN": "123456:production-token",
                "TELEGRAM_WEBHOOK_SECRET": "production-webhook-secret",
                "JWT_SECRET": "production-jwt-secret",
                "PAYMENT_WEBHOOK_SECRET": "production-payment-secret",
            },
        ):
            get_settings.cache_clear()
            app = create_app()
            self.assertIsNone(app.docs_url)
            self.assertIsNone(app.redoc_url)
            self.assertIsNone(app.openapi_url)

    def test_production_settings_reject_placeholders(self) -> None:
        with patch.dict(os.environ, {"APP_ENV": "production"}):
            get_settings.cache_clear()
            with self.assertRaises(RuntimeError) as ctx:
                validate_runtime_settings(get_settings())
            self.assertIn("Invalid production configuration", str(ctx.exception))

    def test_mock_mark_paid_route_requires_admin(self) -> None:
        app = create_app()
        route = next(route for route in app.routes if isinstance(route, APIRoute) and route.endpoint is mark_paid)
        dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
        self.assertIn(require_admin, dependency_calls)

    def test_admin_product_and_file_routes_require_admin(self) -> None:
        app = create_app()
        for endpoint in (read_admin_product, download_admin_file):
            route = next(route for route in app.routes if isinstance(route, APIRoute) and route.endpoint is endpoint)
            dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
            self.assertIn(require_admin, dependency_calls)

    def test_product_view_route_allows_optional_auth(self) -> None:
        app = create_app()
        route = next(route for route in app.routes if isinstance(route, APIRoute) and route.endpoint is view_product)
        dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
        self.assertNotIn(require_admin, dependency_calls)

    def test_admin_file_route_returns_404_for_missing_file(self) -> None:
        class EmptyDb:
            async def scalar(self, _query):
                return None

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(download_admin_file(uuid4(), EmptyDb(), User(telegram_id=111)))
        self.assertEqual(ctx.exception.status_code, 404)

    def test_moderation_notification_is_best_effort(self) -> None:
        product = SimpleNamespace(
            id=uuid4(),
            title="Speaking cards",
            seller=SimpleNamespace(user=SimpleNamespace(telegram_id=123456)),
        )
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123456:test"}):
            get_settings.cache_clear()
            with (
                patch("app.modules.admin.service.send_telegram_message", side_effect=RuntimeError("Telegram down")) as send,
                patch("app.modules.admin.service.logger.exception") as log_exception,
            ):
                asyncio.run(notify_author_about_moderation(product, action="approved"))
                send.assert_called_once()
                log_exception.assert_called_once()

    def test_moderation_status_rules_reject_invalid_transitions(self) -> None:
        async def run_checks() -> list[int]:
            class FakeDb:
                async def commit(self):
                    pass

                def add(self, _item):
                    pass

            actor = User(telegram_id=111)
            product = SimpleNamespace(id=uuid4(), status="published", rejection_reason=None, published_at=None)
            statuses = []
            with patch("app.modules.admin.service.get_product_for_moderation", AsyncMock(return_value=product)):
                for fn in (approve_product, restore_product):
                    try:
                        await fn(FakeDb(), actor=actor, product_id=product.id)
                    except HTTPException as exc:
                        statuses.append(exc.status_code)
                product.status = "rejected"
                try:
                    await hide_product(FakeDb(), actor=actor, product_id=product.id)
                except HTTPException as exc:
                    statuses.append(exc.status_code)
            return statuses

        self.assertEqual(asyncio.run(run_checks()), [400, 400, 400])

    def test_owner_product_lifecycle_rules(self) -> None:
        async def run_checks() -> tuple[int, str, str]:
            class FakeDb:
                async def commit(self):
                    pass

                def add(self, _item):
                    pass

            user = User(id=uuid4(), telegram_id=111)
            published = SimpleNamespace(id=uuid4(), status="published")
            with patch("app.modules.products.service.get_owned_product", AsyncMock(return_value=published)):
                try:
                    await update_product(FakeDb(), user, published.id, SimpleNamespace(model_dump=lambda exclude_unset: {}))
                except HTTPException as exc:
                    invalid_update_status = exc.status_code

            draft = SimpleNamespace(id=uuid4(), status="draft", rejection_reason="fix")
            with (
                patch("app.modules.products.service.require_seller_profile", AsyncMock(return_value=SimpleNamespace(id=uuid4()))),
                patch("app.modules.products.service.get_owned_product", AsyncMock(return_value=draft)),
                patch("app.modules.products.service.enforce_product_limit", AsyncMock(return_value=None)),
                patch("app.modules.products.service.load_product_with_previews", AsyncMock(side_effect=lambda _db, _id: draft)),
            ):
                await submit_product(FakeDb(), user, draft.id)
                submitted_status = draft.status

            hidden = SimpleNamespace(id=uuid4(), status="hidden")
            with (
                patch("app.modules.products.service.get_owned_product", AsyncMock(return_value=hidden)),
                patch("app.modules.products.service.load_product_with_previews", AsyncMock(side_effect=lambda _db, _id: hidden)),
            ):
                await delete_product(FakeDb(), user, hidden.id)
                deleted_status = hidden.status

            return invalid_update_status, submitted_status, deleted_status

        self.assertEqual(asyncio.run(run_checks()), (400, "pending_moderation", "deleted"))

    def test_product_view_dedup_and_self_view_rules(self) -> None:
        async def run_checks() -> tuple[bool, bool, bool, int]:
            class FakeDb:
                def __init__(self, values):
                    self.values = list(values)
                    self.added = []
                    self.commits = 0

                async def scalar(self, _query):
                    return self.values.pop(0)

                def add(self, item):
                    self.added.append(item)

                async def commit(self):
                    self.commits += 1

            seller_user_id = uuid4()
            product = SimpleNamespace(id=uuid4(), seller=SimpleNamespace(user_id=seller_user_id))
            self_view = await track_product_view(
                FakeDb([product]),
                product_id=product.id,
                viewer=User(id=seller_user_id, telegram_id=111),
                client_host="127.0.0.1",
                user_agent="test",
            )
            duplicate = await track_product_view(
                FakeDb([product, uuid4()]),
                product_id=product.id,
                viewer=None,
                client_host="127.0.0.1",
                user_agent="test",
            )
            db = FakeDb([product, None])
            tracked = await track_product_view(
                db,
                product_id=product.id,
                viewer=None,
                client_host="127.0.0.1",
                user_agent="test",
            )
            stable_key = anonymous_view_key(client_host="127.0.0.1", user_agent="test") == anonymous_view_key(client_host="127.0.0.1", user_agent="test")
            return self_view, duplicate, tracked and stable_key, db.commits

        self.assertEqual(asyncio.run(run_checks()), (False, False, True, 1))

    def test_upload_extension_and_size_validation(self) -> None:
        self.assertEqual(validate_extension(filename="lesson.pdf", file_kind=PRODUCT_FILE_KIND), "pdf")
        with self.assertRaises(HTTPException) as ctx:
            validate_extension(filename="malware.exe", file_kind=PRODUCT_FILE_KIND)
        self.assertEqual(ctx.exception.status_code, 400)

        with self.assertRaises(HTTPException) as size_ctx:
            validate_size(file_size=101 * 1024 * 1024, file_kind=PRODUCT_FILE_KIND)
        self.assertEqual(size_ctx.exception.status_code, 413)

    def test_rate_limit_rejects_after_limit(self) -> None:
        async def run_check() -> int:
            dependency = rate_limit(scope=f"test_{uuid4()}", limit=2, window_seconds=60)
            request = SimpleNamespace(headers={}, client=SimpleNamespace(host="127.0.0.1"))
            await dependency(request)
            await dependency(request)
            try:
                await dependency(request)
            except HTTPException as exc:
                return exc.status_code
            return 200

        self.assertEqual(asyncio.run(run_check()), 429)

    def test_mock_webhook_signature_and_payload(self) -> None:
        settings = get_settings()
        provider = MockPaymentProvider()
        raw_body = json.dumps(
            {
                "provider_payment_id": "mock_payment",
                "subscription_payment_id": str(uuid4()),
                "status": "paid",
                "amount": 29900,
                "currency": "UAH",
            },
            separators=(",", ":"),
        ).encode("utf-8")
        signature = hmac.new(settings.payment_webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        provider.verify_webhook(raw_body=raw_body, headers={"x-payment-signature": signature}, settings=settings)
        event = provider.parse_event(raw_body=raw_body)
        self.assertEqual(event.status, "paid")
        self.assertEqual(event.amount, 29900)

        with self.assertRaises(HTTPException) as ctx:
            provider.verify_webhook(raw_body=raw_body, headers={"x-payment-signature": "bad"}, settings=settings)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_webhook_amount_currency_and_payment_id_validation(self) -> None:
        payment_id = uuid4()
        payment = SubscriptionPayment(
            id=payment_id,
            provider="mock",
            provider_payment_id="mock_payment",
            amount=29900,
            currency="UAH",
        )
        valid_event = PaymentWebhookEvent(
            status="paid",
            provider_payment_id="mock_payment",
            amount=29900,
            currency="UAH",
            subscription_payment_id=payment_id,
            raw_payload={},
        )
        validate_webhook_event(payment, valid_event)

        wrong_amount = PaymentWebhookEvent(
            status="paid",
            provider_payment_id="mock_payment",
            amount=100,
            currency="UAH",
            subscription_payment_id=payment_id,
            raw_payload={},
        )
        with self.assertRaises(HTTPException) as ctx:
            validate_webhook_event(payment, wrong_amount)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_paid_mock_payment_is_idempotent(self) -> None:
        async def run_check() -> tuple[bool, int]:
            payment = SubscriptionPayment(
                id=uuid4(),
                provider="mock",
                provider_payment_id="mock_payment",
                status="paid",
                amount=29900,
                currency="UAH",
            )
            with (
                patch("app.modules.subscriptions.service.load_payment", AsyncMock(return_value=payment)),
                patch("app.modules.subscriptions.service.activate_or_extend_subscription", AsyncMock()) as activate,
            ):
                result = await mark_mock_payment_paid(SimpleNamespace(), payment_id=payment.id, actor=User(telegram_id=111))
                return result is payment, activate.await_count

        self.assertEqual(asyncio.run(run_check()), (True, 0))

    def test_subscription_plan_change_extends_from_current_expiry(self) -> None:
        async def run_check() -> tuple[bool, datetime, UUID, UUID]:
            seller_id = uuid4()
            old_plan_id = uuid4()
            new_plan = SubscriptionPlan(
                id=uuid4(),
                code="pro_year",
                name="Pro Year",
                price_amount=200000,
                currency="UAH",
                duration_days=365,
                product_limit=50,
            )
            current_expiry = datetime.now(UTC) + timedelta(days=20)
            existing = Subscription(
                id=uuid4(),
                seller_id=seller_id,
                plan_id=old_plan_id,
                status="active",
                starts_at=datetime.now(UTC) - timedelta(days=10),
                expires_at=current_expiry,
            )
            payment = SubscriptionPayment(
                id=uuid4(),
                seller_id=seller_id,
                plan_id=new_plan.id,
                plan=new_plan,
                provider="mock",
                status="created",
                amount=new_plan.price_amount,
                currency=new_plan.currency,
            )

            class FakeDb:
                async def flush(self):
                    pass

            db = FakeDb()
            with (
                patch("app.modules.subscriptions.service.expire_stale_subscriptions", AsyncMock()) as expire,
                patch("app.modules.subscriptions.service.get_current_subscription_by_seller_id", AsyncMock(return_value=existing)),
            ):
                result = await activate_or_extend_subscription(db, payment)
                expire.assert_awaited_once_with(db, seller_id)
                return result is existing, existing.expires_at, existing.plan_id, new_plan.id

        is_existing, expires_at, plan_id, new_plan_id = asyncio.run(run_check())
        self.assertTrue(is_existing)
        self.assertEqual(plan_id, new_plan_id)
        self.assertGreater(expires_at, datetime.now(UTC) + timedelta(days=380))

    def test_expired_subscription_state_creates_fresh_paid_period(self) -> None:
        async def run_check() -> tuple[Subscription, list[Subscription]]:
            seller_id = uuid4()
            plan = SubscriptionPlan(
                id=uuid4(),
                code="pro_month",
                name="Pro Month",
                price_amount=20000,
                currency="UAH",
                duration_days=30,
                product_limit=20,
            )
            payment = SubscriptionPayment(
                id=uuid4(),
                seller_id=seller_id,
                plan_id=plan.id,
                plan=plan,
                provider="mock",
                status="created",
                amount=plan.price_amount,
                currency=plan.currency,
            )

            class FakeDb:
                def __init__(self) -> None:
                    self.added: list[Subscription] = []

                def add(self, item):
                    self.added.append(item)

                async def flush(self):
                    pass

            db = FakeDb()
            with (
                patch("app.modules.subscriptions.service.expire_stale_subscriptions", AsyncMock()),
                patch("app.modules.subscriptions.service.get_current_subscription_by_seller_id", AsyncMock(return_value=None)),
            ):
                result = await activate_or_extend_subscription(db, payment)
                return result, db.added

        subscription, added = asyncio.run(run_check())
        self.assertIs(subscription, added[0])
        self.assertEqual(subscription.status, "active")
        self.assertGreater(subscription.expires_at, datetime.now(UTC) + timedelta(days=29))

    def test_wayforpay_amount_conversion_and_signature(self) -> None:
        self.assertEqual(amount_to_wayforpay(29900), "299.00")
        self.assertEqual(wayforpay_amount_to_minor_units("299.00"), 29900)
        signature = request_signature("secret", ["merchant", "order", "299.00", "UAH"])
        self.assertEqual(signature, hmac.new(b"secret", b"merchant;order;299.00;UAH", hashlib.md5).hexdigest())

    def test_wayforpay_webhook_verification_and_parse(self) -> None:
        settings = get_settings()
        settings.wayforpay_secret_key = "secret"
        payment_id = uuid4()
        payload = {
            "merchantAccount": "merchant",
            "orderReference": f"wfp_{payment_id}",
            "amount": "299.00",
            "currency": "UAH",
            "authCode": "123456",
            "cardPan": "42****4242",
            "transactionStatus": "Approved",
            "reasonCode": "1100",
        }
        payload["merchantSignature"] = request_signature(
            "secret",
            [
                payload["merchantAccount"],
                payload["orderReference"],
                payload["amount"],
                payload["currency"],
                payload["authCode"],
                payload["cardPan"],
                payload["transactionStatus"],
                payload["reasonCode"],
            ],
        )
        raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        provider = WayForPayProvider()
        provider.verify_webhook(raw_body=raw_body, headers={}, settings=settings)
        event = provider.parse_event(raw_body=raw_body)
        self.assertEqual(event.status, "paid")
        self.assertEqual(event.provider_payment_id, f"wfp_{payment_id}")
        self.assertEqual(event.subscription_payment_id, payment_id)
        self.assertEqual(event.amount, 29900)
        self.assertIsNotNone(event.response_payload)


if __name__ == "__main__":
    unittest.main()
