from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    app_name: str = "teachermarket"
    api_base_url: str = "http://localhost:8000"
    webapp_url: str = "http://localhost:5173"
    database_url: str = "postgresql+asyncpg://teachermarket:teachermarket@localhost:5432/teachermarket"
    cors_allowed_origins: str = "http://localhost:5173"
    telegram_bot_token: str = "123456:replace_me"
    telegram_webhook_secret: str = "replace_me"
    admin_telegram_ids: str = ""
    jwt_secret: str = "replace_with_long_random_secret"
    jwt_expires_minutes: int = 10080
    default_free_product_limit: int = 3
    pro_author_product_limit: int = 50
    feature_subscriptions_enabled: bool = True
    feature_placements_enabled: bool = False
    feature_reviews_enabled: bool = True
    feature_reports_enabled: bool = True
    storage_provider: str = "local"
    local_storage_path: str = "/tmp/teachermarket_storage"
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_bucket: str = ""
    s3_region: str = "auto"
    max_product_file_mb: int = 100
    max_preview_image_mb: int = 10
    allowed_product_extensions: str = "pdf,doc,docx,ppt,pptx,zip"
    allowed_preview_extensions: str = "jpg,jpeg,png,webp"
    payment_provider: str = "mock"
    payment_webhook_secret: str = Field(default="replace_me")
    wayforpay_api_url: str = "https://api.wayforpay.com/api"
    wayforpay_merchant_account: str = ""
    wayforpay_secret_key: str = ""
    wayforpay_merchant_domain: str = "localhost"

    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def admin_ids(self) -> set[int]:
        ids: set[int] = set()
        for raw_id in self.admin_telegram_ids.split(","):
            raw_id = raw_id.strip()
            if raw_id.isdigit():
                ids.add(int(raw_id))
        return ids

    @property
    def allowed_product_extension_set(self) -> set[str]:
        return {extension.strip().lower() for extension in self.allowed_product_extensions.split(",") if extension.strip()}

    @property
    def allowed_preview_extension_set(self) -> set[str]:
        return {extension.strip().lower() for extension in self.allowed_preview_extensions.split(",") if extension.strip()}

    @property
    def wayforpay_is_configured(self) -> bool:
        return bool(self.wayforpay_merchant_account and self.wayforpay_secret_key and self.wayforpay_merchant_domain)


def validate_runtime_settings(settings: Settings) -> None:
    if settings.app_env != "production":
        return

    errors: list[str] = []
    placeholder_values = {
        "replace_me",
        "replace_with_long_random_secret",
        "123456:replace_me",
    }
    secret_fields = {
        "TELEGRAM_BOT_TOKEN": settings.telegram_bot_token,
        "TELEGRAM_WEBHOOK_SECRET": settings.telegram_webhook_secret,
        "JWT_SECRET": settings.jwt_secret,
        "PAYMENT_WEBHOOK_SECRET": settings.payment_webhook_secret,
    }
    for name, value in secret_fields.items():
        if value in placeholder_values or "replace_me" in value:
            errors.append(f"{name} must be set to a real production value.")

    if not settings.api_base_url.startswith("https://"):
        errors.append("API_BASE_URL must use HTTPS in production.")
    if not settings.webapp_url.startswith("https://"):
        errors.append("WEBAPP_URL must use HTTPS in production.")
    if any(origin.startswith("http://localhost") for origin in settings.cors_origins):
        errors.append("CORS_ALLOWED_ORIGINS must not include localhost in production.")
    if settings.payment_provider == "wayforpay" and not settings.wayforpay_is_configured:
        errors.append("WayForPay credentials are required when PAYMENT_PROVIDER=wayforpay.")
    if settings.storage_provider.lower() in {"s3", "r2"} and (
        not settings.s3_endpoint_url
        or not settings.s3_access_key_id
        or not settings.s3_secret_access_key
        or not settings.s3_bucket
    ):
        errors.append("S3/R2 storage settings must be complete when STORAGE_PROVIDER=s3 or r2.")

    if errors:
        raise RuntimeError("Invalid production configuration: " + " ".join(errors))


@lru_cache
def get_settings() -> Settings:
    return Settings()
