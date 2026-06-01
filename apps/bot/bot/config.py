from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    telegram_bot_token: str = "123456:replace_me"
    telegram_webhook_secret: str = "replace_me"
    api_base_url: str = "http://localhost:8000"
    webapp_url: str = "http://localhost:5173"
    admin_telegram_ids: str = ""
    max_product_file_mb: int = 100

    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def admin_ids(self) -> set[int]:
        ids: set[int] = set()
        for raw_id in self.admin_telegram_ids.split(","):
            raw_id = raw_id.strip()
            if raw_id.isdigit():
                ids.add(int(raw_id))
        return ids


@lru_cache
def get_settings() -> BotSettings:
    return BotSettings()
