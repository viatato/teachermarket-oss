from uuid import UUID

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    id: UUID
    original_filename: str
    mime_type: str | None = None
    file_size_bytes: int | None = None
    file_kind: str
