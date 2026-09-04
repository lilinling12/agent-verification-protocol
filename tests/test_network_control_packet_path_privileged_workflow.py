"""Ordinary-CI security contract for the PTL-002 trusted-main workflow."""

from __future__ import annotations

import unittest
from pathlib import Path

_WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "network-control-packet-path-privileged-evidence.yml"
)


class PacketPathPrivilegedWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = _WORKFLOW.read_text(encoding="utf-8")

    def test_trigger_is_trusted_main_or_manual_only(self) -> None:
        self.assertIn("branches: [main]", self.source)
        self.assertIn("workflow_dispatch:", self.source)
        self.assertNotIn("pull_request:", self.source)
        self.assertNotIn("pull_request_target:", self.source)
        self.assertIn(
            "- '.github/workflows/network-control-packet-path-privileged-evidence.yml'",
            self.source,
        )

    def test_permissions_and_checkout_are_read_only(self) -> None:
        self.assertIn("permissions:\n  contents: read", self.source)
        self.assertIn("persist-credentials: false", self.source)
        self.assertNotIn("id-token: write", self.source)
        self.assertNotIn("contents: write", self.source)
        self.assertNotIn("packages: write", self.source)
        self.assertNotIn("attestations: write", self.source)

    def test_exact_main_revision_is_enforced_before_privileged_execution(self) -> None:
        ref_guard = 'if [[ "${GITHUB_REF}" != "refs/heads/main" ]]'
        sha_guard = 'if [[ "$(git rev-parse HEAD)" != "${GITHUB_SHA}" ]]'
        qualification = "scripts/qualify_network_control_packet_path.py"

        self.assertIn(ref_guard, self.source)
        self.assertIn(sha_guard, self.source)
        self.assertLess(self.source.index(ref_guard), self.source.index(qualification))
        self.assertLess(self.source.index(sha_guard), self.source.index(qualification))

    def test_same_run_qualification_precedes_complete_matrix(self) -> None:
        qualification = "scripts/qualify_network_control_packet_path.py"
        runner = "scripts/run_network_control_packet_path_evidence.py"
        self.assertLess(self.source.index(qualification), self.source.index(runner))

        expected_cases = (
            "positive",
            "bypass-fault",
            "early-activation",
            "false-settled",
            "false-recovery",
            "schedule-leak",
            "hidden-retry-fallback",
            "collateral-target",
            "residual-cleanup",
        )
        for case in expected_cases:
            self.assertEqual(self.source.count(f"run_case {case}"), 1)

    def test_privilege_is_confined_to_reviewed_packet_path_clis(self) -> None:
        sudo_lines = [
            line.strip()
            for line in self.source.splitlines()
            if line.strip().startswith("sudo ")
        ]
        self.assertEqual(len(sudo_lines), 2)
        self.assertIn("scripts/qualify_network_control_packet_path.py", sudo_lines[0])
        self.assertIn("scripts/run_network_control_packet_path_evidence.py", sudo_lines[1])
        self.assertNotIn("sudo -E", self.source)
        self.assertNotIn("sudo env", self.source)

    def test_manifest_and_artifact_are_retained_even_on_matrix_failure(self) -> None:
        self.assertIn("- name: Build and verify execution manifest\n        if: always()", self.source)
        self.assertIn("- name: Upload packet-path privileged evidence bundle\n        if: always()", self.source)
        self.assertIn("retention-days: 90", self.source)
        self.assertIn("verify_execution_manifest", self.source)

    def test_workflow_does_not_reuse_terminating_or_release_authority(self) -> None:
        lowered = self.source.lower()
        self.assertNotIn("toxiproxy", lowered)
        self.assertNotIn("docker", lowered)
        # /etc/os-release is legitimate runner provenance. Guard actual authority
        # surfaces rather than matching an incidental English word.
        forbidden_authority = (
            "softprops/action-gh-release",
            "gh release",
            "create release",
            "upload release",
            "sigstore",
            "cosign",
            "id-token: write",
            "contents: write",
            "packages: write",
            "attestations: write",
            "secrets.",
        )
        for marker in forbidden_authority:
            self.assertNotIn(marker, lowered)


if __name__ == "__main__":
    unittest.main()
