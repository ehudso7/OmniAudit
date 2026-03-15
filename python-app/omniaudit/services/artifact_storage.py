"""
Artifact Storage Service

Abstraction over local filesystem and S3-compatible object storage.
Supports local storage for dev and S3 for production.
"""

import os
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, BinaryIO

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ArtifactStorageBackend(ABC):
    """Abstract artifact storage backend."""

    @abstractmethod
    def store(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store artifact data and return the storage path/URL."""
        ...

    @abstractmethod
    def retrieve(self, key: str) -> Optional[bytes]:
        """Retrieve artifact data by key."""
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete an artifact by key."""
        ...

    @abstractmethod
    def get_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """Get a URL to access the artifact. For local storage, returns file path."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if an artifact exists."""
        ...


class LocalStorageBackend(ArtifactStorageBackend):
    """Store artifacts on local filesystem."""

    def __init__(self, base_dir: str = "artifacts/browser_runs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        # Prevent path traversal
        safe_key = key.replace("..", "").lstrip("/")
        return self.base_dir / safe_key

    def store(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    def retrieve(self, key: str) -> Optional[bytes]:
        path = self._resolve_path(key)
        if path.exists():
            return path.read_bytes()
        return None

    def delete(self, key: str) -> bool:
        path = self._resolve_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def get_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        path = self._resolve_path(key)
        if path.exists():
            return str(path)
        return None

    def exists(self, key: str) -> bool:
        return self._resolve_path(key).exists()


class S3StorageBackend(ArtifactStorageBackend):
    """Store artifacts in S3-compatible object storage."""

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        self.bucket = bucket
        self.region = region

        try:
            import boto3
            session_kwargs = {}
            if access_key and secret_key:
                session_kwargs["aws_access_key_id"] = access_key
                session_kwargs["aws_secret_access_key"] = secret_key

            client_kwargs = {"region_name": region}
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url

            self.client = boto3.client("s3", **client_kwargs, **session_kwargs)
            logger.info(f"S3 storage initialized: bucket={bucket}")
        except ImportError:
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")

    def store(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return f"s3://{self.bucket}/{key}"

    def retrieve(self, key: str) -> Optional[bytes]:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except self.client.exceptions.NoSuchKey:
            return None

    def delete(self, key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def get_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except Exception:
            return None

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False


def get_artifact_storage() -> ArtifactStorageBackend:
    """
    Factory to get the configured artifact storage backend.

    Configuration via environment variables:
    - ARTIFACT_STORAGE_BACKEND: "local" (default) or "s3"
    - ARTIFACT_STORAGE_DIR: local storage directory (default: artifacts/browser_runs)
    - S3_BUCKET: S3 bucket name
    - S3_REGION: AWS region (default: us-east-1)
    - S3_ENDPOINT_URL: Custom endpoint (for MinIO, R2, etc.)
    - AWS_ACCESS_KEY_ID: S3 access key
    - AWS_SECRET_ACCESS_KEY: S3 secret key
    """
    backend = os.getenv("ARTIFACT_STORAGE_BACKEND", "local")

    if backend == "s3":
        return S3StorageBackend(
            bucket=os.getenv("S3_BUCKET", "omniaudit-artifacts"),
            region=os.getenv("S3_REGION", "us-east-1"),
            endpoint_url=os.getenv("S3_ENDPOINT_URL"),
            access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

    return LocalStorageBackend(
        base_dir=os.getenv("OMNIAUDIT_ARTIFACTS_DIR", "artifacts/browser_runs")
    )
