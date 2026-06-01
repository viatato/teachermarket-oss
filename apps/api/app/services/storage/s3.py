import hashlib
import hmac
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from app.config import get_settings


class StorageUnavailableError(RuntimeError):
    pass


class S3StorageAdapter:
    service = "s3"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.endpoint_url = self.settings.s3_endpoint_url.rstrip("/")
        self.bucket = self.settings.s3_bucket
        self.region = self.settings.s3_region or "auto"
        if (
            not self.endpoint_url
            or not self.bucket
            or not self.settings.s3_access_key_id
            or not self.settings.s3_secret_access_key
        ):
            raise StorageUnavailableError("S3 storage is not configured.")

    async def save(self, *, content: bytes, file_kind: str, extension: str) -> str:
        storage_key = f"{file_kind}/{uuid4().hex}.{extension}"
        self._request("PUT", storage_key, body=content)
        return storage_key

    async def read(self, storage_key: str) -> bytes:
        return self._request("GET", storage_key)

    def _request(self, method: str, storage_key: str, body: bytes = b"") -> bytes:
        url = self._object_url(storage_key)
        headers = self._signed_headers(method, storage_key, body)
        request = Request(url, data=body if method == "PUT" else None, headers=headers, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                return response.read()
        except HTTPError as exc:
            if exc.code == 404:
                raise FileNotFoundError(storage_key) from exc
            raise StorageUnavailableError(f"S3 returned HTTP {exc.code}.") from exc
        except URLError as exc:
            raise StorageUnavailableError("S3 storage is unavailable.") from exc

    def _object_url(self, storage_key: str) -> str:
        return f"{self.endpoint_url}/{quote(self.bucket, safe='')}/{quote(storage_key, safe='/')}"

    def _signed_headers(self, method: str, storage_key: str, body: bytes) -> dict[str, str]:
        parsed = urlparse(self.endpoint_url)
        host = parsed.netloc
        now = datetime.now(UTC)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        payload_hash = hashlib.sha256(body).hexdigest()
        canonical_uri = f"/{quote(self.bucket, safe='')}/{quote(storage_key, safe='/')}"
        canonical_headers = (
            f"host:{host}\n"
            f"x-amz-content-sha256:{payload_hash}\n"
            f"x-amz-date:{amz_date}\n"
        )
        signed_headers = "host;x-amz-content-sha256;x-amz-date"
        canonical_request = "\n".join(
            [
                method,
                canonical_uri,
                "",
                canonical_headers,
                signed_headers,
                payload_hash,
            ]
        )
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"
        string_to_sign = "\n".join(
            [
                "AWS4-HMAC-SHA256",
                amz_date,
                credential_scope,
                hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
            ]
        )
        signature = hmac.new(
            self._signing_key(date_stamp),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        authorization = (
            "AWS4-HMAC-SHA256 "
            f"Credential={self.settings.s3_access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        return {
            "Authorization": authorization,
            "Host": host,
            "X-Amz-Content-Sha256": payload_hash,
            "X-Amz-Date": amz_date,
        }

    def _signing_key(self, date_stamp: str) -> bytes:
        key_date = _sign(("AWS4" + self.settings.s3_secret_access_key).encode("utf-8"), date_stamp)
        key_region = _sign(key_date, self.region)
        key_service = _sign(key_region, self.service)
        return _sign(key_service, "aws4_request")


def _sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()
