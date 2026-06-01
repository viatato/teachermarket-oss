from uuid import UUID

from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(min_length=1)


class BotUserUpsertRequest(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None


class UserResponse(BaseModel):
    id: UUID
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    is_admin: bool = False


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
