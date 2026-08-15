from __future__ import annotations

import gzip
import importlib.util
import io
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


def _gzip_bytes(payload: bytes, *, mtime: int, filename: str) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(filename=filename, mode="wb", fileobj=buffer, mtime=mtime) as handle:
        handle.write(payload)
    return buffer.getvalue()


class NormalizeSdistTest(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.path = self.root / "example-0.1.0.tar.gz"

    def test_normalization_is_deterministic_and_preserves_payload(self) -> None:
        payload = b"synthetic-tar-payload"
        self.path.write_bytes(_gzip_bytes(payload, mtime=100, filename="first.tar"))
        self.module.normalize(self.path, mtime=123456789)
        first = self.path.read_bytes()

        self.path.write_bytes(_gzip_bytes(payload, mtime=200, filename="second.tar"))
        self.module.normalize(self.path, mtime=123456789)
        second = self.path.read_bytes()

        self.assertEqual(first, second)
        with gzip.open(self.path, "rb") as handle:
            self.assertEqual(handle.read(), payload)

    def test_rejects_negative_mtime(self) -> None:
        self.path.write_bytes(_gzip_bytes(b"payload", mtime=0, filename="x.tar"))
        with self.assertRaisesRegex(self.module.NormalizationError, "non-negative"):
            self.module.normalize(self.path, mtime=-1)

    def test_rejects_non_sdist_path(self) -> None:
        invalid = self.root / "artifact.whl"
        invalid.write_bytes(b"not-gzip")
        with self.assertRaisesRegex(self.module.NormalizationError, "existing .tar.gz"):
            self.module.normalize(invalid, mtime=0)


if __name__ == "__main__":
    unittest.main()
