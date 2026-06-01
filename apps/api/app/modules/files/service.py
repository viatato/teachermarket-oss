from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import File, User
from app.services.storage import get_storage_adapter
from app.services.storage.s3 import StorageUnavailableError


PRODUCT_FILE_KIND = "product_file"
PREVIEW_IMAGE_KIND = "preview_image"
ALLOWED_FILE_KINDS = {PRODUCT_FILE_KIND, PREVIEW_IMAGE_KIND}


def get_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower().removeprefix(".")
    return extension


def validate_file_kind(file_kind: str) -> None:
    if file_kind not in ALLOWED_FILE_KINDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недійсний тип файлу.",
        )


def validate_extension(*, filename: str, file_kind: str) -> str:
    settings = get_settings()
    extension = get_extension(filename)
    allowed_extensions = (
        settings.allowed_product_extension_set
        if file_kind == PRODUCT_FILE_KIND
        else settings.allowed_preview_extension_set
    )
    if not extension or extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Формат файлу не підтримується.",
        )
    return extension


def validate_size(*, file_size: int, file_kind: str) -> None:
    settings = get_settings()
    max_mb = settings.max_product_file_mb if file_kind == PRODUCT_FILE_KIND else settings.max_preview_image_mb
    if file_size > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Файл завеликий.",
        )


def validate_mime_type(*, mime_type: str | None, file_kind: str) -> None:
    if file_kind == PREVIEW_IMAGE_KIND and mime_type and not mime_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Превʼю має бути зображенням.",
        )


async def upload_file(
    *,
    db: AsyncSession,
    owner: User,
    upload: UploadFile,
    file_kind: str,
) -> File:
    validate_file_kind(file_kind)
    extension = validate_extension(filename=upload.filename or "", file_kind=file_kind)
    validate_mime_type(mime_type=upload.content_type, file_kind=file_kind)

    content = await upload.read()
    validate_size(file_size=len(content), file_kind=file_kind)

    storage = get_storage_adapter()
    try:
        storage_key = await storage.save(content=content, file_kind=file_kind, extension=extension)
    except StorageUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Сховище файлів тимчасово недоступне.",
        ) from exc

    file_record = File(
        owner_id=owner.id,
        storage_key=storage_key,
        original_filename=upload.filename or f"upload.{extension}",
        mime_type=upload.content_type,
        file_size_bytes=len(content),
        file_kind=file_kind,
    )
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)
    return file_record
