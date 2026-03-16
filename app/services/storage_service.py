import io
import json
import os
import re
import time
import uuid
from typing import Optional
from urllib.parse import urlparse
import mimetypes

from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import settings


# Singleton MinIO client instance
_minio_client: Optional[Minio] = None


def _build_minio_client() -> Minio:
    """
    Initialize MinIO client using environment settings.
    Update MINIO_ENDPOINT / MINIO_ACCESS_KEY / MINIO_SECRET_KEY in .env to change connection.
    """
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def get_minio_client() -> Minio:
    """Get or create the MinIO client."""
    global _minio_client
    if _minio_client is None:
        _minio_client = _build_minio_client()
    return _minio_client


def ensure_bucket_exists() -> None:
    """
    Ensure the configured bucket exists; create it if missing.
    Change MINIO_BUCKET in .env to switch the target bucket.
    """
    client = get_minio_client()
    bucket = settings.MINIO_BUCKET
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    # Ensure public read access for objects in this bucket (write stays private)
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/*"],
            }
        ],
    }
    try:
        client.set_bucket_policy(bucket, json.dumps(policy))
    except Exception:
        # Best-effort: do not fail startup if policy can't be set
        pass


def init_storage(retries: int = 5, delay_seconds: float = 1.5) -> None:
    """
    Initialize storage on app startup (client + bucket).
    Retries help when MinIO is starting or DNS is not ready.
    """
    last_error: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            ensure_bucket_exists()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(delay_seconds)

    # Do not crash the app if storage is temporarily unavailable
    print(f"MinIO initialization failed after {retries} attempts: {last_error}")


def _normalize_object_name(file_name: str) -> str:
    if not file_name or not file_name.strip():
        raise ValueError("Invalid file name")
    if ".." in file_name or file_name.startswith("/") or "\\" in file_name:
        # Prevent path traversal and absolute paths
        raise ValueError("Invalid file name")
    return file_name.lstrip("/")


def _normalize_folder(folder: str) -> str:
    if not folder or not folder.strip():
        raise ValueError("Invalid folder")
    if ".." in folder or "\\" in folder or folder.startswith("/"):
        raise ValueError("Invalid folder")
    if not re.match(r"^[a-zA-Z0-9/_-]+$", folder):
        raise ValueError("Invalid folder")
    return folder.strip("/").strip()

def _convert_to_webp(data: bytes) -> bytes:
    try:
        image = Image.open(io.BytesIO(data))
    except UnidentifiedImageError as exc:
        raise ValueError("Invalid image file") from exc

    # Preserve alpha when present
    if image.mode in ("RGBA", "LA"):
        converted = image
    else:
        converted = image.convert("RGB")

    out = io.BytesIO()
    converted.save(out, format="WEBP", quality=85, method=6, optimize=True)
    return out.getvalue()


async def upload_file(file: UploadFile, folder: str) -> str:
    """
    Upload file content to MinIO and return the stored object name.
    Flow: validate -> generate UUID name -> upload to bucket.
    """
    if file is None or not file.filename:
        raise ValueError("No file provided")

    folder_name = _normalize_folder(folder)
    original_name = os.path.basename(file.filename)
    _, ext = os.path.splitext(original_name)
    safe_ext = ext.lower()

    object_name = f"{folder_name}/{uuid.uuid4().hex}{safe_ext}"

    data = await file.read()
    if not data:
        raise ValueError("Empty file")

    content_type = file.content_type or "application/octet-stream"
    guessed_type, _ = mimetypes.guess_type(original_name)
    is_image = (
        content_type.startswith("image/")
        or (guessed_type and guessed_type.startswith("image/"))
        or safe_ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    )

    # Convert images to WebP for better size/quality
    if is_image:
        try:
            data = _convert_to_webp(data)
            object_name = f"{folder_name}/{uuid.uuid4().hex}.webp"
            content_type = "image/webp"
        except ValueError:
            # If conversion fails, keep original data/extension
            pass

    client = get_minio_client()

    try:
        client.put_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
    except S3Error as exc:
        raise RuntimeError("Upload failed") from exc

    return object_name


def delete_file(file_name: str) -> None:
    """Delete a file from MinIO by name."""
    object_name = _normalize_object_name(file_name)
    client = get_minio_client()
    try:
        client.remove_object(settings.MINIO_BUCKET, object_name)
    except S3Error as exc:
        raise RuntimeError("Delete failed") from exc


def get_file_url(file_name: str) -> str:
    """
    Generate a public URL for the stored file.
    Set MINIO_PUBLIC_ENDPOINT in .env to expose a different host (e.g., localhost:9000).
    """
    object_name = _normalize_object_name(file_name)
    scheme = "https" if settings.MINIO_SECURE else "http"
    public_endpoint = settings.MINIO_PUBLIC_ENDPOINT or settings.MINIO_ENDPOINT
    return f"{scheme}://{public_endpoint}/{settings.MINIO_BUCKET}/{object_name}"


def get_object_name_from_url(file_url: str) -> Optional[str]:
    """
    Extract object name (folder/filename) from a MinIO file URL.
    Returns None if the URL does not match the configured bucket.
    """
    if not file_url:
        return None
    parsed = urlparse(file_url)
    path = parsed.path or ""
    bucket_prefix = f"/{settings.MINIO_BUCKET}/"
    if not path.startswith(bucket_prefix):
        return None
    object_name = path[len(bucket_prefix):]
    if not object_name:
        return None
    return _normalize_object_name(object_name)
