"""Regression checks for the concrete Network Control helper-image identity boundary."""

from __future__ import annotations

import json
import unittest

from acceptance.network_control.helper_image_verification import prepare_exact_helper_image
from acceptance.network_control.toxiproxy_binding import ToxiproxyPrerequisiteError
from acceptance.network_control.toxiproxy_live_lab import LabHelperArtifact


class _RecordingDocker:
    def __init__(self, inspect_payload: str) -> None:
        self.inspect_payload = inspect_payload
        self.calls: list[tuple[str, ...]] = []

    def run(self, *args: str, allow_failure: bool = False) -> str:
        if allow_failure:
            raise AssertionError("helper preparation must not use allow_failure")
        self.calls.append(args)
        if args and args[0] == "pull":
            return "digest-pinned pull completed"
        if args[:2] == ("image", "inspect"):
            return self.inspect_payload
        raise AssertionError(f"unexpected Docker call: {args!r}")


class HelperImageVerificationTests(unittest.TestCase):
    def test_exact_digest_pull_is_authority_even_when_repodigests_are_normalized(self) -> None:
        artifact = LabHelperArtifact.reviewed_amd64()
        docker = _RecordingDocker(
            json.dumps(
                {
                    "Id": "sha256:" + "1" * 64,
                    "Os": "linux",
                    "Architecture": "amd64",
                    # Docker may normalize the official-image repository spelling and
                    # may expose an index-level RepoDigest. Neither representation is
                    # the authority for a pull already addressed by the exact platform
                    # manifest digest.
                    "RepoDigests": [f"python@{artifact.index_digest}"],
                }
            )
        )

        prepare_exact_helper_image(docker, artifact)  # type: ignore[arg-type]

        self.assertEqual(
            docker.calls,
            [
                ("pull", "--platform", artifact.platform, artifact.image_ref),
                ("image", "inspect", artifact.image_ref, "--format", "{{json .}}"),
            ],
        )

    def test_local_platform_drift_fails_closed(self) -> None:
        artifact = LabHelperArtifact.reviewed_amd64()
        docker = _RecordingDocker(
            json.dumps(
                {
                    "Id": "sha256:" + "2" * 64,
                    "Os": "linux",
                    "Architecture": "arm64",
                    "RepoDigests": [],
                }
            )
        )

        with self.assertRaisesRegex(ToxiproxyPrerequisiteError, "platform mismatch"):
            prepare_exact_helper_image(docker, artifact)  # type: ignore[arg-type]

    def test_malformed_local_inspect_fails_closed(self) -> None:
        artifact = LabHelperArtifact.reviewed_amd64()
        docker = _RecordingDocker("not-json")

        with self.assertRaisesRegex(ToxiproxyPrerequisiteError, "inspect is invalid JSON"):
            prepare_exact_helper_image(docker, artifact)  # type: ignore[arg-type]

    def test_non_object_local_inspect_fails_closed(self) -> None:
        artifact = LabHelperArtifact.reviewed_amd64()
        docker = _RecordingDocker("[]")

        with self.assertRaisesRegex(ToxiproxyPrerequisiteError, "inspect is not an object"):
            prepare_exact_helper_image(docker, artifact)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
