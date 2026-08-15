from __future__ import annotations

import gzip
import importlib.util
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "normalize_sdist.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("normalize_sdist", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load normalize_sdist")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sdist_bytes(*, payload: bytes, member_mtime: int, gzip_mtime: int, uid: int, gid: int) -> bytes:
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        info = tarfile.TarInfo("example-0.1.0/data.txt")
        info.size = len(payload)
        info.mtime = member_mtime
        info.uid = uid
        info.gid = gid
        info.uname = "builder"
        info.gname = "builders"
        info.pax_headers = {"comment": "volatile"}
        archive.addfile(info, io.BytesIO(payload))
    gzip_buffer = io.BytesIO()
    with gzip.GzipFile(filename="volatile.tar", mode="wb", fileobj=gzip_buffer, mtime=gzip_mtime) as handle:
        handle.write(tar_buffer.getvalue())
    return gzip_buffer.getvalue()


class NormalizeSdistTest(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.path = self.root / "example-0.1.0.tar.gz"

    def test_normalization_is_deterministic_and_preserves_file_payload(self) -> None:
        payload = b"source-bytes"
        self.path.write_bytes(
            _sdist_bytes(payload=payload, member_mtime=100, gzip_mtime=101, uid=501, gid=20)
        )
        self.module.normalize(self.path, mtime=123456789)
        first = self.path.read_bytes()

        self.path.write_bytes(
            _sdist_bytes(payload=payload, member_mtime=200, gzip_mtime=201, uid=1000, gid=1000)
        )
        self.module.normalize(self.path, mtime=123456789)
        second = self.path.read_bytes()

        self.assertEqual(first, second)
        with tarfile.open(self.path, mode="r:gz") as archive:
            members = archive.getmembers()
            self.assertEqual([member.name for member in members], ["example-0.1.0/data.txt"])
            member = members[0]
            self.assertEqual(member.mtime, 123456789)
            self.assertEqual(member.uid, 0)
            self.assertEqual(member.gid, 0)
            self.assertEqual(member.uname, "")
            self.assertEqual(member.gname, "")
            self.assertEqual(member.pax_headers, {})
            extracted = archive.extractfile(member)
            self.assertIsNotNone(extracted)
            assert extracted is not None
            self.assertEqual(extracted.read(), payload)

    def test_content_drift_remains_visible_after_normalization(self) -> None:
        first_path = self.root / "first-0.1.0.tar.gz"
        second_path = self.root / "second-0.1.0.tar.gz"
        first_path.write_bytes(
            _sdist_bytes(payload=b"one", member_mtime=100, gzip_mtime=101, uid=1, gid=1)
        )
        second_path.write_bytes(
            _sdist_bytes(payload=b"two", member_mtime=200, gzip_mtime=201, uid=2, gid=2)
        )
        self.module.normalize(first_path, mtime=123)
        self.module.normalize(second_path, mtime=123)
        self.assertNotEqual(first_path.read_bytes(), second_path.read_bytes())

    def test_rejects_negative_mtime(self) -> None:
        self.path.write_bytes(
            _sdist_bytes(payload=b"payload", member_mtime=0, gzip_mtime=0, uid=0, gid=0)
        )
        with self.assertRaisesRegex(self.module.NormalizationError, "non-negative"):
            self.module.normalize(self.path, mtime=-1)

    def test_rejects_non_sdist_path(self) -> None:
        invalid = self.root / "artifact.whl"
        invalid.write_bytes(b"not-gzip")
        with self.assertRaisesRegex(self.module.NormalizationError, "existing .tar.gz"):
            self.module.normalize(invalid, mtime=0)


if __name__ == "__main__":
    unittest.main()
