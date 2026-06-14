import hashlib
import hmac
import json
from decimal import Decimal, ROUND_HALF_UP
from time import time
from urllib import request
from uuid import UUID

from fastapi import HTTPException, status

from app.config import Settings
from app.db.models import SubscriptionPayment
from app.services.payments.base import CreatedPayment, PaymentWebhookEvent


WAYFORPAY_STATUS_MAP = {
    "approved": "paid",
    "declined": "failed",
    "expired": "expired",
    "refunded": "failed",
    "voided": "canceled",
    "refundinprocessing": "failed",
}


class WayForPayProvider:
    code = "wayforpay"

    def create_payment(self, payment: SubscriptionPayment, settings: Settings) -> CreatedPayment:
        if not settings.wayforpay_is_configured:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="WayForPay не налаштовано.",
            )

        order_reference = f"wfp_{payment.id}"
        amount = amount_to_wayforpay(payment.amount)
        product_name = [f"Підписка ТічерМаркет"]
        product_count = [1]
        product_price = [amount]
        order_date = int(time())
        signature = request_signature(
            settings.wayforpay_secret_key,
            [
                settings.wayforpay_merchant_account,
                settings.wayforpay_merchant_domain,
                order_reference,
                str(order_date),
                amount,
                payment.currency,
                *product_name,
                *[str(item) for item in product_count],
                *product_price,
            ],
        )
        payload = {
            "transactionType": "CREATE_INVOICE",
            "merchantAccount": settings.wayforpay_merchant_account,
            "merchantAuthType": "SimpleSignature",
            "merchantDomainName": settings.wayforpay_merchant_domain,
            "merchantSignature": signature,
            "apiVersion": 1,
            "language": "UA",
            "serviceUrl": f"{settings.api_base_url}/subscription-payments/webhook/wayforpay",
            "orderReference": order_reference,
            "orderDate": order_date,
            "amount": amount,
            "currency": payment.currency,
            "productName": product_name,
            "productCount": product_count,
            "productPrice": product_price,
            "paymentSystems": "card;googlePay;applePay;privat24",
        }
        response_payload = post_json(settings.wayforpay_api_url, payload)
        invoice_url = response_payload.get("invoiceUrl")
        if not invoice_url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="WayForPay не повернув invoiceUrl.",
            )
        return CreatedPayment(payment_url=str(invoice_url), provider_payment_id=order_reference)

    def verify_webhook(self, *, raw_body: bytes, headers: dict[str, str], settings: Settings) -> None:
        payload = decode_payload(raw_body)
        provided_signature = payload.get("merchantSignature")
        expected_signature = webhook_signature(settings.wayforpay_secret_key, payload)
        if not provided_signature or not hmac.compare_digest(str(provided_signature), expected_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недійсний підпис WayForPay.")

    def parse_event(self, *, raw_body: bytes) -> PaymentWebhookEvent:
        payload = decode_payload(raw_body)
        order_reference = str(payload.get("orderReference") or "")
        transaction_status = str(payload.get("transactionStatus") or "").lower()
        amount = wayforpay_amount_to_minor_units(payload.get("amount"))
        currency = str(payload.get("currency") or "").upper()
        if not order_reference or not transaction_status or amount is None or not currency:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook payload неповний.")

        status_value = WAYFORPAY_STATUS_MAP.get(transaction_status, transaction_status)

        payment_id = None
        if order_reference.startswith("wfp_"):
            payment_id = UUID(order_reference.removeprefix("wfp_"))

        return PaymentWebhookEvent(
            status=status_value,
            provider_payment_id=order_reference,
            amount=amount,
            currency=currency,
            subscription_payment_id=payment_id,
            raw_payload=payload,
            response_payload=accept_response_payload(order_reference, get_secret_for_response()),
        )


def get_secret_for_response() -> str:
    from app.config import get_settings

    return get_settings().wayforpay_secret_key


def amount_to_wayforpay(amount_minor_units: int) -> str:
    value = (Decimal(amount_minor_units) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return format(value, "f")


def wayforpay_amount_to_minor_units(value: object) -> int | None:
    if value is None:
        return None
    decimal_value = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(decimal_value * 100)


def request_signature(secret_key: str, values: list[str]) -> str:
    message = ";".join(str(value) for value in values)
    return hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.md5).hexdigest()


def webhook_signature(secret_key: str, payload: dict) -> str:
    return request_signature(
        secret_key,
        [
            payload.get("merchantAccount", ""),
            payload.get("orderReference", ""),
            payload.get("amount", ""),
            payload.get("currency", ""),
            payload.get("authCode", ""),
            payload.get("cardPan", ""),
            payload.get("transactionStatus", ""),
            payload.get("reasonCode", ""),
        ],
    )


def accept_response_payload(order_reference: str, secret_key: str) -> dict:
    response_time = int(time())
    status_value = "accept"
    return {
        "orderReference": order_reference,
        "status": status_value,
        "time": response_time,
        "signature": request_signature(secret_key, [order_reference, status_value, str(response_time)]),
    }


def decode_payload(raw_body: bytes) -> dict:
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некоректний webhook payload.") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некоректний webhook payload.")
    return payload


def post_json(url: str, payload: dict) -> dict:
    api_request = request.Request(
        url,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(api_request, timeout=20) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="WayForPay API недоступний.") from exc
    if not isinstance(response_payload, dict):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Некоректна відповідь WayForPay.")
    return response_payload
