from aiogram import Bot
from aiogram.types import Document, PhotoSize, User as TelegramUser

from bot.api_client import ApiClient


async def upload_document_from_telegram(
    *,
    bot: Bot,
    telegram_user: TelegramUser,
    document: Document,
    file_kind: str = "product_file",
) -> dict[str, object]:
    telegram_file = await bot.get_file(document.file_id)
    stream = await bot.download_file(telegram_file.file_path)
    file_bytes = stream.read()
    return await ApiClient().upload_file(
        telegram_user,
        file_bytes=file_bytes,
        filename=document.file_name or "material.pdf",
        file_kind=file_kind,
        content_type=document.mime_type,
    )


async def upload_photo_from_telegram(
    *,
    bot: Bot,
    telegram_user: TelegramUser,
    photo: PhotoSize,
    filename: str = "preview.jpg",
) -> dict[str, object]:
    telegram_file = await bot.get_file(photo.file_id)
    stream = await bot.download_file(telegram_file.file_path)
    file_bytes = stream.read()
    return await ApiClient().upload_file(
        telegram_user,
        file_bytes=file_bytes,
        filename=filename,
        file_kind="preview_image",
        content_type="image/jpeg",
    )
