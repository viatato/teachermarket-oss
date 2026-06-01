import hashlib
import hmac
import json
from uuid import UUID

from fastapi import HTTPException, status

from app.config import Settings
from app.db.models import SubscriptionPayment
from app.services.payments.base import CreatedPayment, PaymentWebhookEvent


class MockPaymentProvider:
    code = "mock"

    def create_payment(self, payment: SubscriptionPayment, settings: Settings) -> CreatedPayment:
        provider_payment_id = f"mock_{payment.id}"
        payment_url = f"{settings.api_base_url}/subscription-payments/mock/{payment.id}/mark-paid"
        return CreatedPayment(payment_url=payment_url, provider_payment_id=provider_payment_id)

    def verify_webhook(self, *, raw_body: bytes, headers: dict[str, str], settings: Settings) -> None:
        signature = headers.get("x-payment-signature")
        expected = hmac.new(settings.payment_webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        if not signature or not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недійсний підпис webhook.")

    def parse_event(self, *, raw_body: bytes) -> PaymentWebhookEvent:
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некоректний webhook payload.") from exc

        provider_payment_id = payload.get("provider_payment_id")
        event_status = payload.get("status")
        amount = payload.get("amount")
        currency = payload.get("currency")
        if not provider_payment_id or not event_status or amount is None or not currency:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook payload неповний.")

        payment_id = payload.get("subscription_payment_id")
        return PaymentWebhookEvent(
            status=str(event_status),
            provider_payment_id=str(provider_payment_id),
            amount=int(amount),
            currency=str(currency).upper(),
            subscription_payment_id=UUID(str(payment_id)) if payment_id else None,
            raw_payload=payload,
        )

