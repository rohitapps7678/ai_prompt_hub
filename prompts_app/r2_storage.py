# prompts_app/r2_storage.py
"""
Cloudflare R2 (S3-compatible) helper.

Flow:
  1. Frontend (admin panel) calls POST /api/admin/media/presign/ with
     filename + content_type.
  2. Backend validates the file type/size, builds a unique object key,
     and returns a short-lived presigned PUT URL + the final public URL.
  3. Frontend uploads the raw file directly to R2 using that PUT URL
     (file bytes never touch the Django server).
  4. Frontend saves the returned public_url as the prompt's image_url.
"""

import uuid
import mimetypes

import boto3
from botocore.client import Config as BotoConfig
from django.conf import settings

# Only allow media types we actually expect (image + video).
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "video/mp4", "video/webm", "video/quicktime",
}


class R2UploadError(Exception):
    pass


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4"),
        region_name="auto",
    )


def build_object_key(filename: str) -> str:
    ext = mimetypes.guess_extension(
        mimetypes.guess_type(filename)[0] or ""
    ) or ("." + filename.rsplit(".", 1)[-1] if "." in filename else "")
    ext = ext.lower() if ext else ""
    return f"prompts/{uuid.uuid4().hex}{ext}"


def create_presigned_upload(filename: str, content_type: str, size_bytes: int | None = None):
    """
    Returns dict: {upload_url, public_url, key}
    Raises R2UploadError on validation failure.
    """
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise R2UploadError(f"Unsupported content type: {content_type}")

    if size_bytes is not None and size_bytes > settings.R2_MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.R2_MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise R2UploadError(f"File too large. Max allowed is {max_mb}MB")

    key = build_object_key(filename)

    upload_url = _client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.R2_BUCKET_NAME,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=settings.R2_PRESIGN_EXPIRY,
    )

    public_url = f"{settings.R2_PUBLIC_URL}/{key}"

    return {"upload_url": upload_url, "public_url": public_url, "key": key}


def delete_object(key: str):
    """Optional helper — delete an object from R2 (e.g. when replacing media)."""
    _client().delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)


def key_from_public_url(url: str) -> str | None:
    prefix = settings.R2_PUBLIC_URL.rstrip("/") + "/"
    if url and url.startswith(prefix):
        return url[len(prefix):]
    return None