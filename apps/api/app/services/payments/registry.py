from fastapi import HTTPException, status

from app.services.payments.base import PaymentProvider
from app.services.payments.mock import MockPaymentProvider
from app.services.payments.wayforpay import WayForPayProvider


PROVIDERS: dict[str, PaymentProvider] = {
    "mock": MockPaymentProvider(),
    "wayforpay": WayForPayProvider(),
}


def get_payment_provider(provider_code: str) -> PaymentProvider:
    provider = PROVIDERS.get(provider_code)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платіжний провайдер не підтримується.")
    return provider
