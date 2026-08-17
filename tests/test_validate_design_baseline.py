from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'validate_design_baseline.py'
spec = importlib.util.spec_from_file_location('validate_design_baseline', SCRIPT)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


def entry_for(path: str, data: bytes) -> dict[str, object]:
    return {
        'source_path': 'historical/source.md',
        'target_path': path,
        'sha256': hashlib.sha256(data).hexdigest(),
        'git_blob_sha1': validator.git_blob_sha1(data),
        'bytes': len(data),
        'lines': data.count(b'\n'),
        'encoding': 'utf-8',
    }


class DesignBaselineValidatorTest(unittest.TestCase):
    def _repo(self, files: dict[str, bytes]) -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, object]]:
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        baseline = root / validator.BASELINE_DIR
        baseline.mkdir(parents=True)
        entries = []
        for rel, data in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            entries.append(entry_for(rel, data))
        manifest = {
            'manifest_version': '1.0',
            'baseline_id': validator.EXPECTED_BASELINE_ID,
            'status': validator.EXPECTED_STATUS,
            'source_archive': {'name': 'archive.zip', 'sha256': '0' * 64, 'bytes': 1},
            'preservation_policy': dict(validator.EXPECTED_POLICY),
            'files': entries,
        }
        raw = (json.dumps(manifest, separators=(',', ':')) + '\n').encode()
        (root / validator.MANIFEST_PATH).write_bytes(raw)
        return td, root, manifest

    def test_git_blob_sha1_matches_git_known_value(self) -> None:
        self.assertEqual('ce013625030ba8dba906f756967f9e9ca394464a', validator.git_blob_sha1(b'hello\n'))

    def test_validate_accepts_exact_content(self) -> None:
        rel = 'docs/design/alpha-v0.1/source.md'
        td, root, _ = self._repo({rel: b'# historical\n'})
        self.addCleanup(td.cleanup)
        manifest_blob = validator.git_blob_sha1((root / validator.MANIFEST_PATH).read_bytes())
        with mock.patch.object(validator, 'EXPECTED_MANIFEST_GIT_BLOB_SHA1', manifest_blob), \
             mock.patch.object(validator, 'EXPECTED_FILE_COUNT', 1):
            self.assertEqual([rel], validator.validate(root))

    def test_validate_rejects_source_mutation(self) -> None:
        rel = 'docs/design/alpha-v0.1/source.md'
        td, root, _ = self._repo({rel: b'original\n'})
        self.addCleanup(td.cleanup)
        manifest_blob = validator.git_blob_sha1((root / validator.MANIFEST_PATH).read_bytes())
        (root / rel).write_bytes(b'mutated\n')
        with mock.patch.object(validator, 'EXPECTED_MANIFEST_GIT_BLOB_SHA1', manifest_blob), \
             mock.patch.object(validator, 'EXPECTED_FILE_COUNT', 1):
            with self.assertRaisesRegex(validator.ValidationError, 'mismatch'):
                validator.validate(root)

    def test_validate_rejects_manifest_mutation_before_trusting_entries(self) -> None:
        rel = 'docs/design/alpha-v0.1/source.md'
        td, root, _ = self._repo({rel: b'original\n'})
        self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(validator.ValidationError, 'manifest Git blob SHA-1 mismatch'):
            validator.validate(root)

    def test_validate_rejects_path_escape(self) -> None:
        td, root, manifest = self._repo({'docs/design/alpha-v0.1/source.md': b'x\n'})
        self.addCleanup(td.cleanup)
        manifest['files'][0]['target_path'] = '../escape.md'
        raw = (json.dumps(manifest, separators=(',', ':')) + '\n').encode()
        (root / validator.MANIFEST_PATH).write_bytes(raw)
        manifest_blob = validator.git_blob_sha1(raw)
        with mock.patch.object(validator, 'EXPECTED_MANIFEST_GIT_BLOB_SHA1', manifest_blob), \
             mock.patch.object(validator, 'EXPECTED_FILE_COUNT', 1):
            with self.assertRaisesRegex(validator.ValidationError, 'escapes baseline directory'):
                validator.validate(root)

    def test_validate_rejects_duplicate_target_path(self) -> None:
        rel = 'docs/design/alpha-v0.1/source.md'
        td, root, manifest = self._repo({rel: b'x\n'})
        self.addCleanup(td.cleanup)
        manifest['files'].append(dict(manifest['files'][0]))
        raw = (json.dumps(manifest, separators=(',', ':')) + '\n').encode()
        (root / validator.MANIFEST_PATH).write_bytes(raw)
        manifest_blob = validator.git_blob_sha1(raw)
        with mock.patch.object(validator, 'EXPECTED_MANIFEST_GIT_BLOB_SHA1', manifest_blob), \
             mock.patch.object(validator, 'EXPECTED_FILE_COUNT', 2):
            with self.assertRaisesRegex(validator.ValidationError, 'duplicate target_path'):
                validator.validate(root)

    def test_validate_rejects_manifest_self_reference(self) -> None:
        td, root, manifest = self._repo({'docs/design/alpha-v0.1/source.md': b'x\n'})
        self.addCleanup(td.cleanup)
        manifest['files'][0]['target_path'] = str(validator.MANIFEST_PATH)
        raw = (json.dumps(manifest, separators=(',', ':')) + '\n').encode()
        (root / validator.MANIFEST_PATH).write_bytes(raw)
        manifest_blob = validator.git_blob_sha1(raw)
        with mock.patch.object(validator, 'EXPECTED_MANIFEST_GIT_BLOB_SHA1', manifest_blob), \
             mock.patch.object(validator, 'EXPECTED_FILE_COUNT', 1):
            with self.assertRaisesRegex(validator.ValidationError, 'manifest cannot list itself'):
                validator.validate(root)


if __name__ == '__main__':
    unittest.main()
