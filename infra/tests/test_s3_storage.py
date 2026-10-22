"""C1: S3FileStorage trên S3 giả lập (moto, chạy trong tiến trình — không cần Docker)."""

from __future__ import annotations

import io
from collections.abc import Iterator
from typing import Any

import boto3
import pytest
from moto import mock_aws

from docchat_infra.storage import S3FileStorage, StorageError

BUCKET = "docchat-test"
KEY = "11111111-1111-1111-1111-111111111111/22222222-2222-2222-2222-222222222222.pdf"
PDF = b"%PDF-1.4 noi dung"


@pytest.fixture()
def s3() -> Iterator[Any]:
    with mock_aws():
        client = boto3.client(
            "s3", region_name="us-east-1", aws_access_key_id="k", aws_secret_access_key="s"
        )
        client.create_bucket(Bucket=BUCKET)
        yield client


def storage(sse: str | None = "AES256", bucket: str = BUCKET) -> S3FileStorage:
    return S3FileStorage(bucket=bucket, access_key="k", secret_key="s", region="us-east-1", sse=sse)


async def test_put_get_roundtrip(s3: Any) -> None:
    st = storage()
    await st.put(KEY, io.BytesIO(PDF), "application/pdf")
    assert await st.get(KEY) == PDF


async def test_put_sets_content_type_and_server_side_encryption(s3: Any) -> None:
    await storage().put(KEY, io.BytesIO(PDF), "application/pdf")
    head = s3.head_object(Bucket=BUCKET, Key=KEY)
    assert head["ContentType"] == "application/pdf"
    assert head["ServerSideEncryption"] == "AES256"


async def test_sse_can_be_disabled_for_minio_dev(s3: Any) -> None:
    await storage(sse="").put(KEY, io.BytesIO(PDF), "application/pdf")
    # Không gửi tham số mã hóa; moto/S3 thật vẫn mã hóa mặc định phía server nên chỉ kiểm không lỗi.
    assert (await storage(sse="").get(KEY)) == PDF


async def test_exists_and_delete(s3: Any) -> None:
    st = storage()
    assert await st.exists(KEY) is False
    await st.put(KEY, io.BytesIO(PDF), "application/pdf")
    assert await st.exists(KEY) is True
    await st.delete(KEY)
    assert await st.exists(KEY) is False


async def test_delete_missing_key_is_idempotent(s3: Any) -> None:
    await storage().delete("khong/ton/tai.pdf")


async def test_get_missing_key_raises_storage_error_without_leaking_key(s3: Any) -> None:
    with pytest.raises(StorageError) as ei:
        await storage().get(KEY)
    assert KEY not in str(ei.value) and "NoSuchKey" in str(ei.value)


async def test_missing_bucket_is_a_storage_error(s3: Any) -> None:
    with pytest.raises(StorageError):
        await storage(bucket="khong-co-bucket").put(KEY, io.BytesIO(PDF), "application/pdf")


async def test_upload_receives_the_file_object_not_a_bytes_copy(s3: Any) -> None:
    """Truyền file-like để boto3 đọc theo khối (multipart khi lớn) thay vì nạp cả tệp vào RAM."""
    seen: list[Any] = []

    class Spy:
        def upload_fileobj(
            self, fileobj: Any, bucket: str, key: str, ExtraArgs: dict[str, str]
        ) -> None:
            seen.append((fileobj, bucket, key, ExtraArgs))

    content = io.BytesIO(PDF)
    st = S3FileStorage(bucket=BUCKET, client=Spy())
    await st.put(KEY, content, "application/pdf")
    fileobj, bucket, key, extra = seen[0]
    assert fileobj is content and bucket == BUCKET and key == KEY
    assert extra == {"ContentType": "application/pdf", "ServerSideEncryption": "AES256"}


async def test_large_object_roundtrip_uses_multipart(s3: Any) -> None:
    big = b"%PDF-" + b"x" * (12 * 1024 * 1024)  # > ngưỡng multipart mặc định của boto3 (8 MB)
    st = storage()
    await st.put(KEY, io.BytesIO(big), "application/pdf")
    assert await st.get(KEY) == big
