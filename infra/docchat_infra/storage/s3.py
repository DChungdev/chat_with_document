"""FileStoragePort cho object storage tương thích S3 (MinIO ở dev, S3 ở prod) — task C1.

boto3 là thư viện đồng bộ nên mọi lời gọi chạy trong thread pool. Truyền tệp dạng file-like
(`upload_fileobj` đọc theo khối, multipart khi lớn) nên không nạp cả tệp vào RAM khi tải lên.
Khóa đối tượng do tầng ứng dụng đặt (`user_id/document_id.pdf`), không bao giờ chứa tên tệp gốc.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

_NOT_FOUND_CODES = {"404", "NoSuchKey", "NotFound"}


class StorageError(Exception):
    """Lỗi hạ tầng lưu trữ. Thông điệp chỉ là mã/loại lỗi, không chứa khóa hay nội dung."""


class S3FileStorage:
    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str = "us-east-1",
        sse: str | None = "AES256",
        client: Any = None,
    ) -> None:
        self._bucket = bucket
        self._sse = sse or None  # chuỗi rỗng = tắt (MinIO dev không có KMS)
        self._client = client or boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(
                retries={"max_attempts": 3, "mode": "standard"},  # retry có backoff
                connect_timeout=5,
                read_timeout=30,
                s3={"addressing_style": "path"},  # MinIO cần path-style
            ),
        )

    async def put(self, key: str, content: BinaryIO, content_type: str) -> None:
        extra: dict[str, str] = {"ContentType": content_type}
        if self._sse:
            extra["ServerSideEncryption"] = self._sse
        await self._call(
            "put", self._client.upload_fileobj, content, self._bucket, key, ExtraArgs=extra
        )

    async def get(self, key: str) -> bytes:
        def read() -> bytes:
            body = self._client.get_object(Bucket=self._bucket, Key=key)["Body"]
            try:
                data: bytes = body.read()
                return data
            finally:
                body.close()

        return await self._call("get", read)  # type: ignore[no-any-return]

    async def delete(self, key: str) -> None:
        # S3 delete_object là idempotent: xóa khóa không tồn tại vẫn thành công.
        await self._call("delete", self._client.delete_object, Bucket=self._bucket, Key=key)

    async def exists(self, key: str) -> bool:
        try:
            await self._call("exists", self._client.head_object, Bucket=self._bucket, Key=key)
        except _NotFound:
            return False
        return True

    async def _call(self, op: str, fn: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return await asyncio.to_thread(fn, *args, **kwargs)
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if op == "exists" and code in _NOT_FOUND_CODES:
                raise _NotFound from None
            logger.warning("storage error", extra={"event": "storage_error", "error_code": code})
            raise StorageError(f"{op}:{code}") from None
        except BotoCoreError as exc:  # timeout, mất kết nối...
            logger.warning(
                "storage error", extra={"event": "storage_error", "exc_type": type(exc).__name__}
            )
            raise StorageError(f"{op}:{type(exc).__name__}") from None


class _NotFound(Exception):
    pass
