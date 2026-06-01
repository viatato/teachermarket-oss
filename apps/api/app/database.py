from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings


settings = get_settings()
engine: AsyncEngine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def check_database_connection() -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
        return True
    except Exception:
        return False
