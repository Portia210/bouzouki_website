"""Cloudflare R2 access (S3 API). The bucket is private: the app only ever hands out
short-lived presigned URLs, and only to a signed-in admin (see `/pdf` in app.py)."""

import os
import re
from functools import lru_cache

ENV_VARS = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")
URL_LIFETIME = 300  # seconds; long enough to open the PDF, short enough to be useless when shared


class StorageError(RuntimeError):
    """R2 is not configured (missing environment variable)."""


def bucket() -> str:
    name = os.getenv("R2_BUCKET")
    if not name:
        raise StorageError("R2_BUCKET is not set")
    return name


@lru_cache(maxsize=1)
def client():
    missing = [v for v in ENV_VARS if not os.getenv(v)]
    if missing:
        raise StorageError(f"missing environment variables: {', '.join(missing)}")
    import boto3  # imported here so the app and the tests start without R2 credentials
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(signature_version="s3v4", retries={"max_attempts": 3, "mode": "standard"}),
    )


def content_disposition(filename: str) -> str:
    """`inline` opens the PDF in the browser; the name is what "Save as" proposes.
    ASCII only (the site's English names), so no header injection and no RFC 5987 needed."""
    safe = re.sub(r"[^A-Za-z0-9 ._()'-]+", "", filename).strip() or "sheet-music.pdf"
    return f'inline; filename="{safe}"'


def presigned_url(key: str, filename: str, expires: int = URL_LIFETIME) -> str:
    return client().generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket(),
            "Key": key,
            "ResponseContentType": "application/pdf",
            "ResponseContentDisposition": content_disposition(filename),
        },
        ExpiresIn=expires,
    )
