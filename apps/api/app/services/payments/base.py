from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.config import Settings
from app.db.models import SubscriptionPayment


@dataclass(frozen=True)
class CreatedPayment:
    payment_url: str
    provider_payment_id: str


@dataclass(frozen=True)
class PaymentWebhookEvent:
    status: str
    provider_payment_id: str
    amount: int
    currency: str
    subscription_payment_id: UUID | None
    raw_payload: dict
    response_payload: dict | None = None


class PaymentProvider(Protocol):
    code: str

    def create_payment(self, payment: SubscriptionPayment, settings: Settings) -> CreatedPayment:
        ...

    def verify_webhook(self, *, raw_body: bytes, headers: dict[str, str], settings: Settings) -> None:
        ...

    def parse_event(self, *, raw_body: bytes) -> PaymentWebhookEvent:
        ...
