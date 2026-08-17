#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

BASELINE_DIR = Path('docs/design/alpha-v0.1')
MANIFEST_PATH = BASELINE_DIR / 'SOURCE-MANIFEST.json'
EXPECTED_MANIFEST_GIT_BLOB_SHA1 = 'b3547db17c91fccfe01cd133e12d52c73628a031'
EXPECTED_BASELINE_ID = 'avp-design-alpha-v0.1'
EXPECTED_STATUS = 'historical-non-normative'
EXPECTED_FILE_COUNT = 20
EXPECTED_POLICY = {
    'content_mutation': 'forbidden',
    'promotion_requires_reconciliation': True,
    'normative_authority': 'none',
}

class ValidationError(Exception):
    pass

def git_blob_sha1(data: bytes) -> str:
    header = f'blob {len(data)}\0'.encode('ascii')
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()

def line_count(data: bytes) -> int:
    return data.count(b'\n')

def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)

def _load_manifest(repo_root: Path) -> tuple[bytes, dict[str, Any]]:
    path = repo_root / MANIFEST_PATH
    _require(path.is_file(), f'missing manifest: {MANIFEST_PATH}')
    raw = path.read_bytes()
    actual_blob = git_blob_sha1(raw)
    _require(
        actual_blob == EXPECTED_MANIFEST_GIT_BLOB_SHA1,
        f'manifest Git blob SHA-1 mismatch: expected {EXPECTED_MANIFEST_GIT_BLOB_SHA1}, got {actual_blob}',
    )
    try:
        manifest = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f'invalid UTF-8 JSON manifest: {exc}') from exc
    return raw, manifest

def validate(repo_root: Path) -> list[str]:
    repo_root = repo_root.resolve()
    _, manifest = _load_manifest(repo_root)

    _require(manifest.get('manifest_version') == '1.0', 'unsupported manifest_version')
    _require(manifest.get('baseline_id') == EXPECTED_BASELINE_ID, 'unexpected baseline_id')
    _require(manifest.get('status') == EXPECTED_STATUS, 'historical baseline status changed')
    _require(manifest.get('preservation_policy') == EXPECTED_POLICY, 'preservation policy changed')

    files = manifest.get('files')
    _require(isinstance(files, list), 'manifest files must be an array')
    _require(len(files) == EXPECTED_FILE_COUNT, f'expected {EXPECTED_FILE_COUNT} files, got {len(files)}')

    seen: set[str] = set()
    checked: list[str] = []
    baseline_root = (repo_root / BASELINE_DIR).resolve()

    for index, entry in enumerate(files):
        _require(isinstance(entry, dict), f'files[{index}] must be an object')
        target = entry.get('target_path')
        _require(isinstance(target, str) and target, f'files[{index}] missing target_path')
        _require(target not in seen, f'duplicate target_path: {target}')
        seen.add(target)

        rel = Path(target)
        _require(not rel.is_absolute(), f'absolute target_path forbidden: {target}')
        candidate = (repo_root / rel).resolve()
        try:
            candidate.relative_to(baseline_root)
        except ValueError as exc:
            raise ValidationError(f'target_path escapes baseline directory: {target}') from exc
        _require(candidate != (repo_root / MANIFEST_PATH).resolve(), 'manifest cannot list itself as a source file')
        _require(candidate.is_file(), f'missing historical source: {target}')

        raw = candidate.read_bytes()
        encoding = entry.get('encoding')
        _require(encoding == 'utf-8', f'{target}: unsupported encoding {encoding!r}')
        try:
            raw.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValidationError(f'{target}: invalid UTF-8: {exc}') from exc

        checks = {
            'bytes': (len(raw), entry.get('bytes')),
            'lines': (line_count(raw), entry.get('lines')),
            'sha256': (hashlib.sha256(raw).hexdigest(), entry.get('sha256')),
            'git_blob_sha1': (git_blob_sha1(raw), entry.get('git_blob_sha1')),
        }
        for field, (actual, expected) in checks.items():
            _require(actual == expected, f'{target}: {field} mismatch: expected {expected}, got {actual}')
        checked.append(target)

    return checked

def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) > 1:
        print('usage: validate_design_baseline.py [repo-root]', file=sys.stderr)
        return 2
    root = Path(argv[0]) if argv else Path.cwd()
    try:
        checked = validate(root)
    except ValidationError as exc:
        print(f'design baseline validation failed: {exc}', file=sys.stderr)
        return 1
    print(f'design baseline validation passed: {len(checked)} immutable files verified')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
