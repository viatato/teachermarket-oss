from typing import Annotated
import hmac
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session
from app.db.models import User
from app.modules.auth.security import decode_access_token


DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    db: DatabaseSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Потрібна авторизація.",
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний токен.",
        )

    user = await db.scalar(select(User).where(User.id == UUID(user_id)))
    if user is None or user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Користувача не знайдено або заблоковано.",
        )
    return user


async def get_optional_user(
    db: DatabaseSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    if not authorization:
        return None
    return await get_current_user(db, authorization)


async def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    settings = get_settings()
    if current_user.telegram_id not in settings.admin_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав.",
        )
    return current_user


async def require_bot_secret(
    x_telegram_bot_secret: Annotated[str | None, Header(alias="X-Telegram-Bot-Secret")] = None,
) -> None:
    settings = get_settings()
    if not x_telegram_bot_secret or not hmac.compare_digest(x_telegram_bot_secret, settings.telegram_webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний bot secret.",
        )
