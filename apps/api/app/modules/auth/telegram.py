import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qsl

from fastapi import HTTPException, status

from app.config import get_settings


MAX_INIT_DATA_AGE = timedelta(hours=24)
MAX_INIT_DATA_FUTURE_SKEW = timedelta(minutes=5)


def verify_telegram_init_data(init_data: str) -> dict[str, Any]:
    settings = get_settings()
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    provided_hash = parsed.pop("hash", None)
    if not provided_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Відсутній hash Telegram.")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(
        b"WebAppData",
        settings.telegram_bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, provided_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недійсний підпис Telegram.")

    auth_date_raw = parsed.get("auth_date")
    if not auth_date_raw or not auth_date_raw.isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недійсний auth_date Telegram.")

    auth_date = datetime.fromtimestamp(int(auth_date_raw), tz=UTC)
    now = datetime.now(UTC)
    if auth_date - now > MAX_INIT_DATA_FUTURE_SKEW:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недійсний auth_date Telegram.")
    if now - auth_date > MAX_INIT_DATA_AGE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Дані Telegram застаріли.")

    raw_user = parsed.get("user")
    if not raw_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Відсутній користувач Telegram.")

    try:
        user = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недійсні дані користувача Telegram.") from exc

    if not isinstance(user.get("id"), int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недійсний Telegram ID.")

    return user
