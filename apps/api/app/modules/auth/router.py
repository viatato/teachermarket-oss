from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.dependencies import DatabaseSession, get_current_user, require_bot_secret
from app.db.models import User
from app.modules.auth.schemas import AuthResponse, BotUserUpsertRequest, TelegramAuthRequest, UserResponse
from app.modules.auth.security import create_access_token
from app.modules.auth.service import upsert_user_from_telegram
from app.modules.auth.telegram import verify_telegram_init_data
from app.security.rate_limit import rate_limit


router = APIRouter(prefix="/auth", tags=["auth"])


def user_response(user: User) -> UserResponse:
    settings = get_settings()
    return UserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        is_admin=user.telegram_id in settings.admin_ids,
    )


@router.post(
    "/telegram",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit(scope="auth_telegram", limit=5, window_seconds=60))],
)
async def telegram_auth(payload: TelegramAuthRequest, db: DatabaseSession) -> AuthResponse:
    telegram_user = verify_telegram_init_data(payload.init_data)
    user = await upsert_user_from_telegram(
        db,
        BotUserUpsertRequest(
            telegram_id=telegram_user["id"],
            username=telegram_user.get("username"),
            first_name=telegram_user.get("first_name"),
            last_name=telegram_user.get("last_name"),
            language_code=telegram_user.get("language_code"),
        ),
    )
    return AuthResponse(
        access_token=create_access_token(str(user.id)),
        user=user_response(user),
    )


@router.get("/me", response_model=UserResponse)
async def auth_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return user_response(current_user)


@router.post(
    "/bot-user",
    response_model=AuthResponse,
    dependencies=[
        Depends(rate_limit(scope="auth_bot_user", limit=120, window_seconds=60)),
        Depends(require_bot_secret),
    ],
)
async def bot_user_upsert(payload: BotUserUpsertRequest, db: DatabaseSession) -> AuthResponse:
    user = await upsert_user_from_telegram(db, payload)
    return AuthResponse(
        access_token=create_access_token(str(user.id)),
        user=user_response(user),
    )
