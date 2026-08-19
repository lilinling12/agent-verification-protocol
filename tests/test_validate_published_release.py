from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_published_release.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_published_release", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load validate_published_release")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PublishedReleaseValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.output = Path(self.temp_dir.name) / "release"
        self.repository = "example/avp"
        self.tag = "v0.3.0-rc.1"
        self.commit = "a" * 40
        self.version = "0.3.0rc1"
        self.wheel = f"avp_reference-{self.version}-py3-none-any.whl"
        self.sdist = f"avp_reference-{self.version}.tar.gz"
        self.payloads = {
            self.wheel: b"wheel-bytes",
            self.sdist: b"sdist-bytes",
        }
        records = [
            {
                "filename": self.wheel,
                "kind": "wheel",
                "sha256": _sha256(self.payloads[self.wheel]),
                "size": len(self.payloads[self.wheel]),
            },
            {
                "filename": self.sdist,
                "kind": "sdist",
                "sha256": _sha256(self.payloads[self.sdist]),
                "size": len(self.payloads[self.sdist]),
            },
        ]
        records.sort(key=lambda item: item["filename"])
        manifest = {
            "artifacts": records,
            "distribution": {"name": "avp-reference", "version": self.version},
            "schemaVersion": "avp-release-evidence/v1",
            "source": {"commit": self.commit, "repository": self.repository},
        }
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
        checksum_lines = [f"{record['sha256']}  {record['filename']}" for record in records]
        checksum_lines.append(f"{_sha256(manifest_bytes)}  MANIFEST.json")
        self.payloads["MANIFEST.json"] = manifest_bytes
        self.payloads["SHA256SUMS"] = ("\n".join(checksum_lines) + "\n").encode()

    def _release(self):
        return {
            "tag_name": self.tag,
            "target_commitish": self.commit,
            "draft": False,
            "prerelease": True,
            "assets": [
                {
                    "name": name,
                    "url": f"https://api.example/assets/{name}",
                    "digest": f"sha256:{_sha256(payload)}",
                    "size": len(payload),
                }
                for name, payload in self.payloads.items()
            ],
        }

    def _ref(self):
        return {"object": {"type": "commit", "sha": self.commit}}

    def _validate(self, release=None, ref=None, payloads=None, *, prerelease=True):
        release = self._release() if release is None else release
        ref = self._ref() if ref is None else ref
        payloads = self.payloads if payloads is None else payloads

        def fake_json(url, token):
            return ref if "/git/ref/tags/" in url else release

        def fake_download(url, destination, token):
            destination.write_bytes(payloads[url.rsplit("/", 1)[-1]])

        with patch.object(self.module, "_request_json", side_effect=fake_json), patch.object(
            self.module, "_download", side_effect=fake_download
        ):
            return self.module.validate_published_release(
                repository=self.repository,
                tag=self.tag,
                commit=self.commit,
                version=self.version,
                output_dir=self.output,
                prerelease=prerelease,
            )

    def test_valid_release_round_trip(self) -> None:
        result = self._validate()
        self.assertEqual(result["manifest"]["source"]["commit"], self.commit)
        self.assertTrue(Path(result["wheel"]).is_file())

    def test_rejects_tag_commit_substitution(self) -> None:
        ref = {"object": {"type": "commit", "sha": "b" * 40}}
        with self.assertRaisesRegex(self.module.PublishedReleaseError, "does not resolve"):
            self._validate(ref=ref)

    def test_rejects_draft_or_wrong_release_class(self) -> None:
        release = self._release()
        release["draft"] = True
        with self.assertRaisesRegex(self.module.PublishedReleaseError, "must be published"):
            self._validate(release=release)

        release = self._release()
        release["prerelease"] = False
        with self.assertRaisesRegex(self.module.PublishedReleaseError, "prerelease flag"):
            self._validate(release=release)

    def test_rejects_noncanonical_or_unsupported_version(self) -> None:
        for version in ("0.3.0-rc1", "0.3.0rc2.dev0", "0.3.0+local", "../../escape"):
            with self.subTest(version=version), self.assertRaisesRegex(
                self.module.PublishedReleaseError,
                "canonical AVP RC/stable PEP 440 subset",
            ):
                self.module.validate_published_release(
                    repository=self.repository,
                    tag=self.tag,
                    commit=self.commit,
                    version=version,
                    output_dir=self.output,
                )

    def test_rejects_tag_version_or_class_mismatch(self) -> None:
        with self.assertRaisesRegex(self.module.PublishedReleaseError, "tag/version/class mismatch"):
            self.module.validate_published_release(
                repository=self.repository,
                tag="v0.3.0-rc.2",
                commit=self.commit,
                version=self.version,
                output_dir=self.output,
            )

        with self.assertRaisesRegex(self.module.PublishedReleaseError, "stable distribution version"):
            self.module.validate_published_release(
                repository=self.repository,
                tag=self.tag,
                commit=self.commit,
                version=self.version,
                output_dir=self.output,
                prerelease=False,
            )

        with self.assertRaisesRegex(self.module.PublishedReleaseError, "RC distribution version"):
            self.module.validate_published_release(
                repository=self.repository,
                tag="v0.3.0",
                commit=self.commit,
                version="0.3.0",
                output_dir=self.output,
                prerelease=True,
            )

    def test_accepts_stable_identity_shape_before_network_access(self) -> None:
        with patch.object(
            self.module,
            "_request_json",
            side_effect=self.module.PublishedReleaseError("network probe reached"),
        ):
            with self.assertRaisesRegex(self.module.PublishedReleaseError, "network probe reached"):
                self.module.validate_published_release(
                    repository=self.repository,
                    tag="v0.3.0",
                    commit=self.commit,
                    version="0.3.0",
                    output_dir=self.output,
                    prerelease=False,
                )

    def test_rejects_unexpected_or_duplicate_assets(self) -> None:
        release = self._release()
        release["assets"].append(
            {"name": "extra.txt", "url": "https://api.example/assets/extra.txt", "digest": "sha256:" + "0" * 64, "size": 0}
        )
        with self.assertRaisesRegex(self.module.PublishedReleaseError, "asset set mismatch"):
            self._validate(release=release)

        release = self._release()
        release["assets"].append(dict(release["assets"][0]))
        with self.assertRaisesRegex(self.module.PublishedReleaseError, "duplicate release asset"):
            self._validate(release=release)

    def test_rejects_downloaded_asset_digest_tampering(self) -> None:
        payloads = dict(self.payloads)
        payloads[self.wheel] = b"tampered-wheel"
        with self.assertRaisesRegex(self.module.PublishedReleaseError, "GitHub asset digest mismatch"):
            self._validate(payloads=payloads)

    def test_rejects_manifest_source_tampering_even_with_matching_asset_digest(self) -> None:
        release = self._release()
        payloads = dict(self.payloads)
        manifest = json.loads(payloads["MANIFEST.json"])
        manifest["source"]["commit"] = "b" * 40
        payloads["MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
        for asset in release["assets"]:
            if asset["name"] == "MANIFEST.json":
                asset["digest"] = f"sha256:{_sha256(payloads['MANIFEST.json'])}"
                asset["size"] = len(payloads["MANIFEST.json"])
        with self.assertRaisesRegex(self.module.PublishedReleaseError, "manifest source identity mismatch"):
            self._validate(release=release, payloads=payloads)

    def test_rejects_checksum_file_tampering_even_with_matching_asset_digest(self) -> None:
        release = self._release()
        payloads = dict(self.payloads)
        payloads["SHA256SUMS"] = b"not-the-authoritative-checksums\n"
        for asset in release["assets"]:
            if asset["name"] == "SHA256SUMS":
                asset["digest"] = f"sha256:{_sha256(payloads['SHA256SUMS'])}"
                asset["size"] = len(payloads["SHA256SUMS"])
        with self.assertRaisesRegex(self.module.PublishedReleaseError, "SHA256SUMS"):
            self._validate(release=release, payloads=payloads)

    def test_rejects_non_exact_commit(self) -> None:
        with self.assertRaisesRegex(self.module.PublishedReleaseError, "exact lowercase 40-character"):
            self.module.validate_published_release(
                repository=self.repository,
                tag=self.tag,
                commit="main",
                version=self.version,
                output_dir=self.output,
            )


if __name__ == "__main__":
    unittest.main()
