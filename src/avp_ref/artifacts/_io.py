"""Shared byte-stream helpers for ArtifactStore implementations."""

from __future__ import annotations

import hashlib
from typing import BinaryIO, Iterator

from .errors import ArtifactDigestMismatch, ArtifactSizeLimitExceeded
from .models import validate_sha256_digest

CHUNK_SIZE = 64 * 1024
DEFAULT_MAX_ARTIFACT_BYTES = 64 * 1024 * 1024


def validate_limit(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("max_artifact_bytes must be a positive integer")
    return value


def iter_stream(stream: BinaryIO) -> Iterator[bytes]:
    if not hasattr(stream, "read"):
        raise TypeError("artifact stream must provide read()")
    while True:
        chunk = stream.read(CHUNK_SIZE)
        if chunk == b"":
            return
        if not isinstance(chunk, bytes):
            raise TypeError("artifact stream read() must return bytes")
        yield chunk


def consume_stream(stream: BinaryIO, *, max_bytes: int) -> tuple[bytes, str]:
    buffer = bytearray()
    hasher = hashlib.sha256()
    size = 0
    for chunk in iter_stream(stream):
        size += len(chunk)
        if size > max_bytes:
            raise ArtifactSizeLimitExceeded(limit=max_bytes, observed=size)
        buffer.extend(chunk)
        hasher.update(chunk)
    return bytes(buffer), "sha256:" + hasher.hexdigest()


def verify_expected_digest(expected: str | None, actual: str) -> None:
    if expected is None:
        return
    validate_sha256_digest(expected)
    if expected != actual:
        raise ArtifactDigestMismatch(expected=expected, actual=actual)
