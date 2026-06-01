from pathlib import Path
from uuid import uuid4

from app.config import get_settings


class LocalStorageAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_path = Path(self.settings.local_storage_path)

    async def save(self, *, content: bytes, file_kind: str, extension: str) -> str:
        storage_key = f"{file_kind}/{uuid4().hex}.{extension}"
        target_path = self.base_path / storage_key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)
        return storage_key

    def resolve_path(self, storage_key: str) -> Path:
        return self.base_path / storage_key

    async def read(self, storage_key: str) -> bytes:
        path = self.resolve_path(storage_key)
        if not path.is_file():
            raise FileNotFoundError(storage_key)
        return path.read_bytes()
