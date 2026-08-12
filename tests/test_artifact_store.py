from __future__ import annotations

import io
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from jsonschema import Draft202012Validator

from avp_ref.artifacts import (
    ArtifactDigestMismatch,
    ArtifactIntegrityError,
    ArtifactRef,
    ArtifactSizeLimitExceeded,
    InMemoryArtifactStore,
    LocalFilesystemArtifactStore,
    sha256_digest,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_SCHEMA = ROOT / "schemas/artifact-ref.schema.json"


class ArtifactIdentityTest(unittest.TestCase):
    def test_exact_bytes_define_identity(self) -> None:
        first = b'{"a":1,"b":2}'
        second = b'{"b":2,"a":1}'
        self.assertNotEqual(sha256_digest(first), sha256_digest(second))

    def test_reference_serializes_to_protocol_schema(self) -> None:
        schema = json.loads(ARTIFACT_SCHEMA.read_text(encoding="utf-8"))
        ref = ArtifactRef(
            digest=sha256_digest(b"AVP"),
            size=3,
            media_type="application/octet-stream",
            uri="artifact://example/value",
        )
        Draft202012Validator(schema).validate(ref.to_dict())

    def test_invalid_digest_cannot_become_path_input(self) -> None:
        with self.assertRaises(ValueError):
            ArtifactRef(
                digest="sha256:../../etc/passwd",
                size=1,
                media_type="application/octet-stream",
            )


class InMemoryArtifactStoreTest(unittest.TestCase):
    def test_round_trip_and_metadata_do_not_change_identity(self) -> None:
        store = InMemoryArtifactStore()
        first = store.put_bytes(b"same bytes", media_type="application/octet-stream")
        second = store.put_bytes(b"same bytes", media_type="text/plain")
        self.assertEqual(first.digest, second.digest)
        self.assertEqual(b"same bytes", store.get_bytes(first))
        self.assertTrue(store.contains(first.digest))

    def test_expected_digest_mismatch_does_not_publish(self) -> None:
        store = InMemoryArtifactStore()
        wrong = sha256_digest(b"different")
        with self.assertRaises(ArtifactDigestMismatch):
            store.put_bytes(b"payload", media_type="application/octet-stream", expected_digest=wrong)
        self.assertFalse(store.contains(wrong))

    def test_size_limit_fails_before_publication(self) -> None:
        store = InMemoryArtifactStore(max_artifact_bytes=3)
        with self.assertRaises(ArtifactSizeLimitExceeded):
            store.put_stream(io.BytesIO(b"four"), media_type="application/octet-stream")

    def test_internal_corruption_fails_closed(self) -> None:
        store = InMemoryArtifactStore()
        ref = store.put_bytes(b"original", media_type="application/octet-stream")
        store._objects[ref.digest] = b"tampered"
        with self.assertRaises(ArtifactIntegrityError):
            store.get_bytes(ref)
        with self.assertRaises(ArtifactIntegrityError):
            store.contains(ref.digest)


class LocalFilesystemArtifactStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.store = LocalFilesystemArtifactStore(self.root)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _path(self, digest: str) -> Path:
        value = digest.removeprefix("sha256:")
        return self.root / "sha256" / value[:2] / value[2:4] / value

    def test_round_trip_and_stream_reader(self) -> None:
        ref = self.store.put_stream(
            io.BytesIO(b"artifact payload"),
            media_type="application/octet-stream",
        )
        with self.store.open_reader(ref) as reader:
            self.assertEqual(b"artifact payload", reader.read())
        self.assertEqual(b"artifact payload", self.store.get_bytes(ref))

    def test_expected_digest_mismatch_leaves_no_published_object(self) -> None:
        expected = sha256_digest(b"expected")
        with self.assertRaises(ArtifactDigestMismatch):
            self.store.put_bytes(
                b"actual",
                media_type="application/octet-stream",
                expected_digest=expected,
            )
        self.assertFalse(self.store.contains(expected))
        self.assertEqual([], list((self.root / ".tmp").iterdir()))

    def test_tampered_and_truncated_content_are_rejected(self) -> None:
        ref = self.store.put_bytes(b"original content", media_type="application/octet-stream")
        path = self._path(ref.digest)
        path.write_bytes(b"tampered")
        with self.assertRaises(ArtifactIntegrityError):
            self.store.get_bytes(ref)

        path.write_bytes(b"original content"[:-1])
        with self.assertRaises(ArtifactIntegrityError):
            self.store.get_bytes(ref)

    def test_symlink_replacement_is_rejected(self) -> None:
        if not hasattr(Path, "symlink_to"):
            self.skipTest("symlinks are unavailable")
        ref = self.store.put_bytes(b"linked content", media_type="application/octet-stream")
        target = self._path(ref.digest)
        external = self.root / "external"
        external.write_bytes(b"linked content")
        target.unlink()
        try:
            target.symlink_to(external)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        with self.assertRaises(ArtifactIntegrityError):
            self.store.get_bytes(ref)

    def test_corrupt_existing_digest_is_not_overwritten(self) -> None:
        payload = b"immutable"
        digest = sha256_digest(payload)
        path = self._path(digest)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"corrupt")

        with self.assertRaises(ArtifactIntegrityError):
            self.store.put_bytes(
                payload,
                media_type="application/octet-stream",
                expected_digest=digest,
            )
        self.assertEqual(b"corrupt", path.read_bytes())

    def test_concurrent_identical_publish_deduplicates(self) -> None:
        payload = b"concurrent immutable artifact" * 1024

        def publish(_: int) -> str:
            return self.store.put_bytes(
                payload,
                media_type="application/octet-stream",
            ).digest

        with ThreadPoolExecutor(max_workers=8) as pool:
            digests = list(pool.map(publish, range(24)))
        self.assertEqual(1, len(set(digests)))
        digest = digests[0]
        self.assertTrue(self.store.contains(digest))
        self.assertEqual(
            1,
            len(list((self.root / "sha256").rglob(digest.removeprefix("sha256:")))),
        )

    def test_size_limit_removes_temp_file(self) -> None:
        store = LocalFilesystemArtifactStore(self.root / "limited", max_artifact_bytes=4)
        with self.assertRaises(ArtifactSizeLimitExceeded):
            store.put_stream(
                io.BytesIO(b"12345"),
                media_type="application/octet-stream",
            )
        self.assertEqual([], list((self.root / "limited" / ".tmp").iterdir()))


if __name__ == "__main__":
    unittest.main()
