from typing import Final


PAYMENT_CREATED: Final = "created"
PAYMENT_PAID: Final = "paid"
PAYMENT_FAILED: Final = "failed"
PAYMENT_CANCELED: Final = "canceled"
PAYMENT_EXPIRED: Final = "expired"

PAYMENT_STATUSES = frozenset(
    {
        PAYMENT_CREATED,
        PAYMENT_PAID,
        PAYMENT_FAILED,
        PAYMENT_CANCELED,
        PAYMENT_EXPIRED,
    }
)
FAILED_PAYMENT_STATUSES = frozenset({PAYMENT_FAILED, PAYMENT_CANCELED, PAYMENT_EXPIRED})

_PROVIDER_STATUS_ALIASES = {
    "paid": PAYMENT_PAID,
    "succeeded": PAYMENT_PAID,
    "success": PAYMENT_PAID,
    "failed": PAYMENT_FAILED,
    "canceled": PAYMENT_CANCELED,
    "cancelled": PAYMENT_CANCELED,
    "expired": PAYMENT_EXPIRED,
}


def canonical_payment_status(provider_status: str) -> str | None:
    return _PROVIDER_STATUS_ALIASES.get(provider_status.strip().lower())


def payment_transition_allowed(current_status: str, target_status: str) -> bool:
    if current_status == target_status:
        return True
    if current_status == PAYMENT_CREATED:
        return target_status in PAYMENT_STATUSES - {PAYMENT_CREATED}
    if current_status in FAILED_PAYMENT_STATUSES:
        return target_status == PAYMENT_PAID
    return False
