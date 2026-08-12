"""Atomic local-filesystem content-addressed ArtifactStore."""

from __future__ import annotations

import hashlib
import io
import os
import tempfile
from pathlib import Path
from typing import BinaryIO

from ._io import (
    CHUNK_SIZE,
    DEFAULT_MAX_ARTIFACT_BYTES,
    iter_stream,
    validate_limit,
    verify_expected_digest,
)
from .errors import ArtifactIntegrityError, ArtifactNotFound, ArtifactSizeLimitExceeded, ArtifactStoreError
from .models import ArtifactRef, validate_media_type, validate_sha256_digest


class LocalFilesystemArtifactStore:
    """Publish immutable Artifact bytes atomically under a digest-derived path.

    Temporary files live below the configured root so publication never crosses
    filesystems. ``os.link`` is used as an atomic create-if-absent operation:
    concurrent publishers deduplicate without replacing an already-published
    object. Existing content is always integrity-checked before reuse.
    """

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        max_artifact_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
    ) -> None:
        self._root = Path(root).expanduser().resolve()
        self._max_artifact_bytes = validate_limit(max_artifact_bytes)
        self._root.mkdir(parents=True, exist_ok=True)
        self._tmp = self._root / ".tmp"
        self._tmp.mkdir(mode=0o700, exist_ok=True)
        if self._tmp.is_symlink():
            raise ArtifactStoreError("artifact temporary directory must not be a symlink")

    def put_bytes(
        self,
        data: bytes,
        *,
        media_type: str,
        expected_digest: str | None = None,
    ) -> ArtifactRef:
        if not isinstance(data, bytes):
            raise TypeError("artifact content must be bytes")
        return self.put_stream(
            io.BytesIO(data),
            media_type=media_type,
            expected_digest=expected_digest,
        )

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

        fd, temp_name = tempfile.mkstemp(prefix="artifact-", dir=self._tmp)
        temp_path = Path(temp_name)
        size = 0
        hasher = hashlib.sha256()
        published = False
        active_error: BaseException | None = None
        try:
            with os.fdopen(fd, "wb") as handle:
                for chunk in iter_stream(stream):
                    size += len(chunk)
                    if size > self._max_artifact_bytes:
                        raise ArtifactSizeLimitExceeded(
                            limit=self._max_artifact_bytes,
                            observed=size,
                        )
                    handle.write(chunk)
                    hasher.update(chunk)
                handle.flush()
                os.fsync(handle.fileno())

            actual = "sha256:" + hasher.hexdigest()
            verify_expected_digest(expected_digest, actual)
            ref = ArtifactRef(actual, size, media_type)
            target = self._object_path(actual)
            target.parent.mkdir(parents=True, exist_ok=True)
            self._assert_store_path(target)

            try:
                os.link(temp_path, target)
                published = True
                self._fsync_directory(target.parent)
            except FileExistsError:
                self._verify_path(target, expected_digest=actual, expected_size=size)

            # Read-after-publish verification detects storage corruption before
            # a reference escapes to callers.
            self._verify_path(target, expected_digest=actual, expected_size=size)
            return ref
        except OSError as exc:
            active_error = exc
            raise ArtifactStoreError(f"artifact filesystem operation failed: {exc}") from exc
        except BaseException as exc:
            active_error = exc
            raise
        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError as cleanup_error:
                # Never mask the primary failure. If publication succeeded and
                # cleanup itself is the only failure, surface it explicitly.
                if active_error is None and published:
                    raise ArtifactStoreError(
                        f"published artifact but failed to remove temp file: {cleanup_error}"
                    ) from cleanup_error

    def open_reader(self, ref: ArtifactRef) -> BinaryIO:
        if not isinstance(ref, ArtifactRef):
            raise TypeError("ref must be an ArtifactRef")
        path = self._object_path(ref.digest)
        self._assert_store_path(path)
        if path.is_symlink():
            raise ArtifactIntegrityError(f"artifact path must not be a symlink: {ref.digest}")
        try:
            handle = path.open("rb")
        except FileNotFoundError as exc:
            raise ArtifactNotFound(f"artifact not found: {ref.digest}") from exc
        try:
            self._verify_handle(
                handle,
                expected_digest=ref.digest,
                expected_size=ref.size,
            )
            handle.seek(0)
            return handle
        except Exception:
            handle.close()
            raise

    def get_bytes(self, ref: ArtifactRef) -> bytes:
        with self.open_reader(ref) as handle:
            return handle.read()

    def contains(self, digest: str) -> bool:
        validate_sha256_digest(digest)
        path = self._object_path(digest)
        self._assert_store_path(path)
        if not path.exists() and not path.is_symlink():
            return False
        self._verify_path(path, expected_digest=digest, expected_size=None)
        return True

    def _object_path(self, digest: str) -> Path:
        validate_sha256_digest(digest)
        hex_digest = digest.removeprefix("sha256:")
        return self._root / "sha256" / hex_digest[:2] / hex_digest[2:4] / hex_digest

    def _assert_store_path(self, path: Path) -> None:
        try:
            path.parent.resolve().relative_to(self._root)
        except ValueError as exc:
            raise ArtifactStoreError("artifact path escapes configured store root") from exc

    def _verify_path(
        self,
        path: Path,
        *,
        expected_digest: str,
        expected_size: int | None,
    ) -> None:
        self._assert_store_path(path)
        if path.is_symlink():
            raise ArtifactIntegrityError(
                f"artifact path must not be a symlink: {expected_digest}"
            )
        try:
            with path.open("rb") as handle:
                self._verify_handle(
                    handle,
                    expected_digest=expected_digest,
                    expected_size=expected_size,
                )
        except FileNotFoundError as exc:
            raise ArtifactNotFound(f"artifact not found: {expected_digest}") from exc

    @staticmethod
    def _verify_handle(
        handle: BinaryIO,
        *,
        expected_digest: str,
        expected_size: int | None,
    ) -> None:
        hasher = hashlib.sha256()
        size = 0
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if chunk == b"":
                break
            if not isinstance(chunk, bytes):
                raise ArtifactIntegrityError("artifact reader produced non-bytes content")
            size += len(chunk)
            hasher.update(chunk)
        actual = "sha256:" + hasher.hexdigest()
        if actual != expected_digest or (expected_size is not None and size != expected_size):
            raise ArtifactIntegrityError(
                f"artifact integrity mismatch for {expected_digest}: size={size}, digest={actual}"
            )

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        if os.name != "posix":
            return
        flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            flags |= os.O_DIRECTORY
        fd = os.open(path, flags)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
