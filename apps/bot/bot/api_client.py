from dataclasses import dataclass
from urllib.parse import unquote

import httpx
from aiogram.types import User as TelegramUser

from bot.config import get_settings


@dataclass(frozen=True)
class DownloadedFile:
    content: bytes
    filename: str
    content_type: str


def filename_from_content_disposition(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    for raw_part in value.split(";"):
        part = raw_part.strip()
        lower_part = part.lower()
        if lower_part.startswith("filename*="):
            filename = part.split("=", 1)[1].strip('"')
            if "''" in filename:
                filename = filename.split("''", 1)[1]
            return unquote(filename) or fallback
        if lower_part.startswith("filename="):
            return part.split("=", 1)[1].strip('"') or fallback
    return fallback


class ApiClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def health(self) -> dict[str, object]:
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=10) as client:
            response = await client.get("/health")
            response.raise_for_status()
            return response.json()

    async def upsert_bot_user(
        self,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        language_code: str | None,
    ) -> dict[str, object]:
        payload = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "language_code": language_code,
        }
        headers = {"X-Telegram-Bot-Secret": self.settings.telegram_webhook_secret}
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=10) as client:
            response = await client.post("/auth/bot-user", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def upsert_bot_user_from_telegram(self, user: TelegramUser) -> dict[str, object]:
        return await self.upsert_bot_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
        )

    async def get_seller_profile(self, telegram_user: TelegramUser) -> dict[str, object] | None:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=10) as client:
            response = await client.get(
                "/seller/profile",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def create_seller_profile(
        self,
        telegram_user: TelegramUser,
        *,
        display_name: str,
        bio: str | None,
        contact_username: str | None,
    ) -> dict[str, object]:
        token = await self.create_bot_access_token(telegram_user)
        payload = {
            "display_name": display_name,
            "bio": bio,
            "contact_username": contact_username,
        }
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=10) as client:
            response = await client.post(
                "/seller/profile",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def create_bot_access_token(self, telegram_user: TelegramUser) -> str:
        response = await self.upsert_bot_user_from_telegram(telegram_user)
        return str(response["access_token"])

    async def upload_file(
        self,
        telegram_user: TelegramUser,
        *,
        file_bytes: bytes,
        filename: str,
        file_kind: str,
        content_type: str | None,
    ) -> dict[str, object]:
        token = await self.create_bot_access_token(telegram_user)
        files = {
            "file": (filename, file_bytes, content_type or "application/octet-stream"),
        }
        data = {"file_kind": file_kind}
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=60) as client:
            response = await client.post(
                "/files/upload",
                data=data,
                files=files,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def create_product(self, telegram_user: TelegramUser, payload: dict[str, object]) -> dict[str, object]:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.post(
                "/products",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def submit_product(self, telegram_user: TelegramUser, product_id: str) -> dict[str, object]:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.post(
                f"/products/{product_id}/submit",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def admin_approve_product(self, telegram_user: TelegramUser, product_id: str) -> dict[str, object]:
        return await self._admin_post_product_action(telegram_user, product_id, "approve")

    async def admin_get_product(self, telegram_user: TelegramUser, product_id: str) -> dict[str, object]:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.get(
                f"/admin/products/{product_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def admin_download_file(self, telegram_user: TelegramUser, file_id: str) -> DownloadedFile:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=60) as client:
            response = await client.get(
                f"/admin/files/{file_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "application/octet-stream").split(";", 1)[0]
            filename = filename_from_content_disposition(
                response.headers.get("content-disposition"),
                fallback=f"{file_id}",
            )
            return DownloadedFile(content=response.content, filename=filename, content_type=content_type)

    async def admin_hide_product(self, telegram_user: TelegramUser, product_id: str) -> dict[str, object]:
        return await self._admin_post_product_action(telegram_user, product_id, "hide")

    async def admin_reject_product(
        self,
        telegram_user: TelegramUser,
        product_id: str,
        *,
        reason: str,
    ) -> dict[str, object]:
        return await self._admin_post_product_action(telegram_user, product_id, "reject", json={"reason": reason})

    async def admin_request_product_changes(
        self,
        telegram_user: TelegramUser,
        product_id: str,
        *,
        reason: str,
    ) -> dict[str, object]:
        return await self._admin_post_product_action(
            telegram_user,
            product_id,
            "request-changes",
            json={"reason": reason},
        )

    async def _admin_post_product_action(
        self,
        telegram_user: TelegramUser,
        product_id: str,
        action: str,
        json: dict[str, object] | None = None,
    ) -> dict[str, object]:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.post(
                f"/admin/products/{product_id}/{action}",
                json=json,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def get_seller_products(self, telegram_user: TelegramUser) -> list[dict[str, object]]:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.get(
                "/seller/products",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def get_seller_contact_requests(self, telegram_user: TelegramUser) -> list[dict[str, object]]:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.get(
                "/seller/contact-requests",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def get_seller_subscription(self, telegram_user: TelegramUser) -> dict[str, object]:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.get(
                "/seller/subscription",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def get_subscription_plans(self) -> list[dict[str, object]]:
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.get("/subscription-plans")
            response.raise_for_status()
            return response.json()

    async def create_subscription_checkout(
        self,
        telegram_user: TelegramUser,
        *,
        plan_id: str,
    ) -> dict[str, object]:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.post(
                "/seller/subscription/checkout",
                json={"plan_id": plan_id},
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def mark_mock_payment_paid(self, telegram_user: TelegramUser, payment_id: str) -> dict[str, object]:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.post(
                f"/subscription-payments/mock/{payment_id}/mark-paid",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def admin_list_subscriptions(self, telegram_user: TelegramUser) -> list[dict[str, object]]:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.get(
                "/admin/subscriptions",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()

    async def admin_activate_seller_subscription(
        self,
        telegram_user: TelegramUser,
        *,
        seller_id: str,
        plan_id: str,
    ) -> dict[str, object]:
        token = await self.create_bot_access_token(telegram_user)
        async with httpx.AsyncClient(base_url=self.settings.api_base_url, timeout=30) as client:
            response = await client.post(
                f"/admin/sellers/{seller_id}/activate-subscription",
                json={"plan_id": plan_id},
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()
