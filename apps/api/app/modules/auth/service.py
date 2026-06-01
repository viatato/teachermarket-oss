from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.modules.auth.schemas import BotUserUpsertRequest


async def upsert_user_from_telegram(db: AsyncSession, payload: BotUserUpsertRequest) -> User:
    user = await db.scalar(select(User).where(User.telegram_id == payload.telegram_id))
    if user is None:
        user = User(
            telegram_id=payload.telegram_id,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            language_code=payload.language_code,
        )
        db.add(user)
    else:
        user.username = payload.username
        user.first_name = payload.first_name
        user.last_name = payload.last_name
        user.language_code = payload.language_code

    await db.commit()
    await db.refresh(user)
    return user
