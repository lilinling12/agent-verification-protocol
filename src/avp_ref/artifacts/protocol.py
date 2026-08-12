"""ArtifactStore SPI implemented by reference storage backends."""

from __future__ import annotations

from typing import BinaryIO, Protocol, runtime_checkable

from .models import ArtifactRef


@runtime_checkable
class ArtifactStore(Protocol):
    """Store and retrieve immutable exact-byte Artifacts.

    Implementations must validate integrity before returning a reader. The SPI
    accepts bytes/byte streams only; serialization belongs to the caller/codec.
    """

    def put_bytes(
        self,
        data: bytes,
        *,
        media_type: str,
        expected_digest: str | None = None,
    ) -> ArtifactRef: ...

    def put_stream(
        self,
        stream: BinaryIO,
        *,
        media_type: str,
        expected_digest: str | None = None,
    ) -> ArtifactRef: ...

    def open_reader(self, ref: ArtifactRef) -> BinaryIO: ...

    def get_bytes(self, ref: ArtifactRef) -> bytes: ...

    def contains(self, digest: str) -> bool: ...
