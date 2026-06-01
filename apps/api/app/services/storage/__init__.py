from app.config import get_settings
from app.services.storage.local import LocalStorageAdapter
from app.services.storage.s3 import S3StorageAdapter


def get_storage_adapter():
    provider = get_settings().storage_provider.lower()
    if provider in {"s3", "r2"}:
        return S3StorageAdapter()
    return LocalStorageAdapter()
