import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.database import get_db_session
from app.db.models import AuditLog, ContactRequest, User
from app.dependencies import get_current_user
from app.main import create_app


class FakeContactRequestDb:
    def __init__(self, product_id: UUID) -> None:
        self.product_id = product_id
        self.current_requester_id: UUID | None = None
        self.contact_requests: dict[tuple[UUID | None, UUID], ContactRequest] = {}
        self.pending_contact_requests: list[ContactRequest] = []
        self.audit_logs: list[AuditLog] = []
        self.commits = 0

    async def scalar(self, _query):
        return self.contact_requests.get((self.current_requester_id, self.product_id))

    def add(self, item) -> None:
        if isinstance(item, ContactRequest):
            self.pending_contact_requests.append(item)
        elif isinstance(item, AuditLog):
            self.audit_logs.append(item)

    async def flush(self) -> None:
        for contact_request in self.pending_contact_requests:
            contact_request.id = contact_request.id or uuid4()
            contact_request.created_at = contact_request.created_at or datetime.now(UTC)
            contact_request.status = contact_request.status or "new"
            self.contact_requests[(contact_request.requester_id, contact_request.product_id)] = contact_request
        self.pending_contact_requests.clear()

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, _item) -> None:
        return None


class ContactRequestApiTests(unittest.TestCase):
    def test_contact_request_is_idempotent_per_buyer_and_product(self) -> None:
        product_id = uuid4()
        seller_id = uuid4()
        seller_user = User(id=uuid4(), telegram_id=900001, username="author")
        product = SimpleNamespace(
            id=product_id,
            seller_id=seller_id,
            title="Speaking cards",
            seller=SimpleNamespace(
                id=seller_id,
                user_id=seller_user.id,
                contact_url=None,
                contact_username="author",
                user=seller_user,
            ),
        )
        buyers = [
            User(id=uuid4(), telegram_id=100001, username="buyer_one"),
            User(id=uuid4(), telegram_id=100002, username="buyer_two"),
        ]
        current_buyer = [buyers[0]]
        db = FakeContactRequestDb(product_id)

        async def override_db_session():
            yield db

        async def override_current_user():
            db.current_requester_id = current_buyer[0].id
            return current_buyer[0]

        app = create_app()
        app.dependency_overrides[get_db_session] = override_db_session
        app.dependency_overrides[get_current_user] = override_current_user

        with (
            patch(
                "app.modules.contact_requests.service.load_contactable_product",
                AsyncMock(return_value=product),
            ),
            patch(
                "app.modules.contact_requests.service.notify_seller_about_contact_request",
                AsyncMock(),
            ) as notify,
            TestClient(app) as client,
        ):
            first = client.post(
                f"/products/{product_id}/contact-request",
                json={"message": "Хочу придбати матеріал"},
            )
            repeated = client.post(
                f"/products/{product_id}/contact-request",
                json={"message": "Хочу придбати матеріал"},
            )
            current_buyer[0] = buyers[1]
            second_buyer = client.post(
                f"/products/{product_id}/contact-request",
                json={"message": "Підкажіть, будь ласка"},
            )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(repeated.status_code, 201)
        self.assertEqual(second_buyer.status_code, 201)
        self.assertEqual(first.json()["id"], repeated.json()["id"])
        self.assertNotEqual(first.json()["id"], second_buyer.json()["id"])
        self.assertEqual(len(db.contact_requests), 2)
        self.assertEqual(len(db.audit_logs), 2)
        self.assertEqual(notify.await_count, 2)


if __name__ == "__main__":
    unittest.main()
