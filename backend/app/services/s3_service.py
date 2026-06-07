"""S3 file upload/delete service. Stores product images and brand assets.
Brand-scoped bucket paths: s3://bucket/brands/{brand_id}/products/filename"""

import uuid
from uuid import UUID
import boto3
from botocore.exceptions import ClientError
from app.config import get_settings

settings = get_settings()


def _get_client():
    """Get S3 client. Uses credentials from config."""
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def upload_file(
    file_content: bytes,
    brand_id: UUID,
    folder: str,
    original_filename: str,
    content_type: str = "image/jpeg",
) -> str:
    """Upload a file to S3. Returns the public URL.
    Path: brands/{brand_id}/{folder}/{unique_filename}"""

    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        raise ValueError("AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env")

    # Generate unique filename to prevent overwrites
    ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "jpg"
    unique_name = f"{uuid.uuid4().hex[:12]}.{ext}"
    key = f"brands/{brand_id}/{folder}/{unique_name}"

    try:
        client = _get_client()
        client.put_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=key,
            Body=file_content,
            ContentType=content_type,
        )
    except ClientError as e:
        raise ValueError(f"S3 upload failed: {e}")

    return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def delete_file(file_url: str) -> bool:
    """Delete a file from S3 by its URL."""
    try:
        # Extract key from URL
        prefix = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/"
        if not file_url.startswith(prefix):
            return False

        key = file_url[len(prefix):]
        client = _get_client()
        client.delete_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
        return True
    except ClientError:
        return False
