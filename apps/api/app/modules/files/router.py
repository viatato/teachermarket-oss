from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.dependencies import DatabaseSession, get_current_user
from app.db.models import File as FileModel
from app.db.models import User
from app.modules.files.schemas import FileUploadResponse
from app.modules.files.service import PREVIEW_IMAGE_KIND, upload_file
from app.security.rate_limit import rate_limit
from app.services.storage import get_storage_adapter
from app.services.storage.s3 import StorageUnavailableError


router = APIRouter(prefix="/files", tags=["files"])


def file_response(file_record: FileModel) -> FileUploadResponse:
    return FileUploadResponse(
        id=file_record.id,
        original_filename=file_record.original_filename,
        mime_type=file_record.mime_type,
        file_size_bytes=file_record.file_size_bytes,
        file_kind=file_record.file_kind,
    )


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    dependencies=[Depends(rate_limit(scope="upload", limit=20, window_seconds=60))],
)
async def upload(
    request: Request,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> FileUploadResponse:
    form = await request.form()
    file_kind_raw = form.get("file_kind")
    file = form.get("file")
    if not isinstance(file_kind_raw, str) or not isinstance(file, (UploadFile, StarletteUploadFile)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Потрібні поля file_kind і file.",
        )
    file_kind = file_kind_raw
    file_record = await upload_file(db=db, owner=current_user, upload=file, file_kind=file_kind)
    return file_response(file_record)


@router.get("/preview/{file_id}", name="preview_file")
async def preview_file(file_id: UUID, db: DatabaseSession) -> Response:
    file_record = await db.scalar(select(FileModel).where(FileModel.id == file_id))
    if file_record is None or file_record.file_kind != PREVIEW_IMAGE_KIND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Превʼю не знайдено.",
        )

    try:
        content = await get_storage_adapter().read(file_record.storage_key)
        media_type = file_record.mime_type or "application/octet-stream"
    except FileNotFoundError:
        if file_record.storage_key.startswith("demo/previews/"):
            content = demo_preview_svg(file_record.original_filename).encode("utf-8")
            media_type = "image/svg+xml"
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Файл превʼю недоступний.",
            )
    except StorageUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Сховище превʼю тимчасово недоступне.",
        ) from exc

    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )


def demo_preview_svg(title: str) -> str:
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="720" viewBox="0 0 960 720" role="img" aria-label="{safe_title}">
  <rect width="960" height="720" fill="#eef8ff"/>
  <rect x="136" y="92" width="688" height="536" rx="28" fill="#ffffff" stroke="#cfe2ef" stroke-width="4"/>
  <rect x="184" y="156" width="284" height="24" rx="12" fill="#175cd3"/>
  <rect x="184" y="226" width="592" height="18" rx="9" fill="#dbeaf3"/>
  <rect x="184" y="270" width="520" height="18" rx="9" fill="#dbeaf3"/>
  <rect x="184" y="314" width="560" height="18" rx="9" fill="#dbeaf3"/>
  <rect x="184" y="408" width="160" height="86" rx="18" fill="#d8f8f2"/>
  <rect x="384" y="408" width="160" height="86" rx="18" fill="#e5f0ff"/>
  <rect x="584" y="408" width="160" height="86" rx="18" fill="#dff7ff"/>
  <text x="184" y="584" fill="#102335" font-family="Arial, sans-serif" font-size="34" font-weight="700">ТічерМаркет</text>
</svg>"""
