"""Thread-safe in-memory content-addressed ArtifactStore."""

from __future__ import annotations

import io
import threading
from typing import BinaryIO

from ._io import DEFAULT_MAX_ARTIFACT_BYTES, consume_stream, validate_limit, verify_expected_digest
from .errors import ArtifactIntegrityError, ArtifactNotFound, ArtifactSizeLimitExceeded
from .models import ArtifactRef, sha256_digest, validate_media_type, validate_sha256_digest


class InMemoryArtifactStore:
    """Small deterministic ArtifactStore for tests and local execution."""

    def __init__(self, *, max_artifact_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES) -> None:
        self._max_artifact_bytes = validate_limit(max_artifact_bytes)
        self._objects: dict[str, bytes] = {}
        self._lock = threading.RLock()

    def put_bytes(
        self,
        data: bytes,
        *,
        media_type: str,
        expected_digest: str | None = None,
    ) -> ArtifactRef:
        validate_media_type(media_type)
        if expected_digest is not None:
            validate_sha256_digest(expected_digest)
        if not isinstance(data, bytes):
            raise TypeError("artifact content must be bytes")
        if len(data) > self._max_artifact_bytes:
            raise ArtifactSizeLimitExceeded(
                limit=self._max_artifact_bytes,
                observed=len(data),
            )
        actual = sha256_digest(data)
        verify_expected_digest(expected_digest, actual)
        ref = ArtifactRef(actual, len(data), media_type)
        with self._lock:
            existing = self._objects.get(actual)
            if existing is not None and existing != data:
                raise ArtifactIntegrityError(
                    f"stored bytes do not match content identity {actual}"
                )
            self._objects.setdefault(actual, data)
        return ref

    def put_stream(
        self,
        stream: BinaryIO,
        *,
        media_type: str,
        expected_digest: str | None = None,
    ) -> ArtifactRef:
        validate_media_type(media_type)
        if expected_digest is not None:
            validate_sha256_digest(expected_digest)
        data, actual = consume_stream(stream, max_bytes=self._max_artifact_bytes)
        verify_expected_digest(expected_digest, actual)
        return self.put_bytes(data, media_type=media_type, expected_digest=actual)

    def open_reader(self, ref: ArtifactRef) -> BinaryIO:
        return io.BytesIO(self.get_bytes(ref))

    def get_bytes(self, ref: ArtifactRef) -> bytes:
        if not isinstance(ref, ArtifactRef):
            raise TypeError("ref must be an ArtifactRef")
        with self._lock:
            data = self._objects.get(ref.digest)
        if data is None:
            raise ArtifactNotFound(f"artifact not found: {ref.digest}")
        actual = sha256_digest(data)
        if len(data) != ref.size or actual != ref.digest:
            raise ArtifactIntegrityError(
                f"artifact integrity mismatch for {ref.digest}: size={len(data)}, digest={actual}"
            )
        return data

    def contains(self, digest: str) -> bool:
        validate_sha256_digest(digest)
        with self._lock:
            data = self._objects.get(digest)
        if data is None:
            return False
        if sha256_digest(data) != digest:
            raise ArtifactIntegrityError(f"artifact integrity mismatch for {digest}")
        return True
